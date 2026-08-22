from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Organization, OrganizationMembership, RefreshToken, User

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 200_000
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    encoded = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${iterations}${salt}${encoded}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt, digest = hashed_password.split("$")
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        expected = base64.urlsafe_b64decode(digest.encode("ascii"))
    except ValueError:
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    )
    return hmac.compare_digest(computed, expected)


def _token_secret(token_type: str) -> str:
    if token_type == "refresh":
        return settings.jwt_refresh_secret
    return settings.jwt_secret


def create_token(subject: str, *, token_type: str, expires_minutes: int) -> str:
    issued_at = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=expires_minutes)).timestamp()),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, _token_secret(token_type), algorithm="HS256")


def create_access_token(subject: str) -> str:
    return create_token(subject, token_type="access", expires_minutes=60)


def create_refresh_token(subject: str) -> str:
    return create_token(subject, token_type="refresh", expires_minutes=60 * 24 * 7)


def _refresh_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def issue_refresh_token(db: Session, user: User) -> str:
    token = create_refresh_token(str(user.id))
    payload = decode_token(token, token_type="refresh")
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_refresh_hash(token),
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        )
    )
    db.flush()
    return token


def rotate_refresh_token(db: Session, token: str) -> tuple[User, str]:
    decode_token(token, token_type="refresh")
    token_hash = _refresh_hash(token)
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )

    # Ensure expires_at is timezone-aware for comparison (SQLite returns naive datetimes)
    expires_at = None
    if record is not None:
        expires_at = (
            record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=UTC)
        )

    if record is None or record.revoked_at is not None or expires_at <= datetime.now(UTC):
        if record and record.revoked_at is not None:
            db.query(RefreshToken).filter(
                RefreshToken.user_id == record.user_id, RefreshToken.revoked_at.is_(None)
            ).update({RefreshToken.revoked_at: datetime.now(UTC)}, synchronize_session=False)
        raise ValueError("Refresh token is revoked or expired")
    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise ValueError("User is not active")
    replacement = create_refresh_token(str(user.id))
    replacement_hash = _refresh_hash(replacement)
    replacement_payload = decode_token(replacement, token_type="refresh")
    record.revoked_at = datetime.now(UTC)
    record.replaced_by_hash = replacement_hash
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=replacement_hash,
            expires_at=datetime.fromtimestamp(replacement_payload["exp"], UTC),
        )
    )
    db.flush()
    return user, replacement


def revoke_refresh_token(db: Session, token: str) -> None:
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == _refresh_hash(token), RefreshToken.revoked_at.is_(None))
        .with_for_update()
        .first()
    )
    if record:
        record.revoked_at = datetime.now(UTC)
        db.flush()


def decode_token(token: str, *, token_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            _token_secret(token_type),
            algorithms=["HS256"],
            options={"require": ["sub", "type", "exp", "iat"]},
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid token") from exc

    if payload.get("type") != token_type:
        raise ValueError("Invalid token type")

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    try:
        payload = decode_token(credentials.credentials, token_type="access")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    sub = payload.get("sub")
    try:
        if isinstance(sub, str):
            sub = UUID(sub)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from exc

    user = db.get(User, sub)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")

    return user


async def get_current_membership(
    current_user: User = Depends(get_current_user),
    organization_id: str | None = None,
    db: Session = Depends(get_db),
) -> OrganizationMembership:
    if organization_id is None:
        membership = (
            db.query(OrganizationMembership)
            .join(Organization, Organization.id == OrganizationMembership.organization_id)
            .filter(
                OrganizationMembership.user_id == current_user.id,
                OrganizationMembership.is_active.is_(True),
                Organization.is_active.is_(True),
            )
            .order_by(OrganizationMembership.created_at.asc())
            .first()
        )
    else:
        membership = (
            db.query(OrganizationMembership)
            .join(Organization, Organization.id == OrganizationMembership.organization_id)
            .filter(
                OrganizationMembership.user_id == current_user.id,
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.is_active.is_(True),
                Organization.is_active.is_(True),
            )
            .first()
        )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of the requested organization",
        )

    if membership.role and membership.role.name.lower() == "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer accounts may only use customer portal endpoints",
        )

    return membership


async def require_admin(
    membership: OrganizationMembership = Depends(get_current_membership),
) -> OrganizationMembership:
    if membership.user.is_superadmin:
        return membership
    role_name = membership.role.name.lower() if membership.role else "staff"
    if role_name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action",
        )
    return membership


def require_role(allowed_roles: list[str]):
    async def _role_checker(
        membership: OrganizationMembership = Depends(get_current_membership),
    ) -> OrganizationMembership:
        if membership.user.is_superadmin:
            return membership
        role_name = membership.role.name.lower() if membership.role else "staff"
        normalized_allowed = [r.lower() for r in allowed_roles]
        if role_name not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
            )
        return membership

    return _role_checker
