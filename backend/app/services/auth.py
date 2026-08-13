from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models import Organization, OrganizationMembership, Role, User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def get_default_membership(db: Session, user_id: UUID) -> OrganizationMembership | None:
    return (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user_id, OrganizationMembership.is_active.is_(True))
        .order_by(OrganizationMembership.created_at.asc())
        .first()
    )


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    organization_name: str,
    organization_slug: str,
) -> tuple[User, Organization, Role, OrganizationMembership, str, str]:
    normalized_email = email.lower().strip()

    existing_user = get_user_by_email(db, normalized_email)
    if existing_user is not None:
        raise ValueError("User with this email already exists")

    organization = Organization(
        name=organization_name.strip(),
        slug=organization_slug.strip().lower(),
        email=normalized_email,
        is_active=True,
    )
    db.add(organization)
    db.flush()

    role = Role(
        organization_id=organization.id,
        name="admin",
        description="Organization administrator",
        is_system_role=True,
    )
    db.add(role)
    db.flush()

    user = User(
        email=normalized_email,
        full_name=full_name.strip(),
        password_hash=hash_password(password),
        is_active=True,
        is_superadmin=False,
    )
    db.add(user)
    db.flush()

    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
        is_active=True,
    )
    db.add(membership)
    db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return user, organization, role, membership, access_token, refresh_token


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email.lower().strip())
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def issue_tokens_for_user(user: User) -> tuple[str, str]:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return access_token, refresh_token
