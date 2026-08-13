from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import OrganizationMembership, User

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 200_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
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
    }
    return jwt.encode(payload, _token_secret(token_type), algorithm="HS256")


def create_access_token(subject: str) -> str:
    return create_token(subject, token_type="access", expires_minutes=60)


def create_refresh_token(subject: str) -> str:
    return create_token(subject, token_type="refresh", expires_minutes=60 * 24 * 7)


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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        payload = decode_token(credentials.credentials, token_type="access")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    user = db.get(User, payload.get("sub"))
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
            .filter(
                OrganizationMembership.user_id == current_user.id,
                OrganizationMembership.is_active.is_(True),
            )
            .order_by(OrganizationMembership.created_at.asc())
            .first()
        )
    else:
        membership = (
            db.query(OrganizationMembership)
            .filter(
                OrganizationMembership.user_id == current_user.id,
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.is_active.is_(True),
            )
            .first()
        )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of the requested organization",
        )

    return membership
