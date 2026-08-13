from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_token, get_current_user
from app.db.session import get_db
from app.models import OrganizationMembership, User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MeResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPairResponse,
    UserPublic,
)
from app.services.auth import authenticate_user, get_default_membership, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superadmin=user.is_superadmin,
    )


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user, organization, _role, _membership, access_token, refresh_token = register_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            organization_name=payload.organization_name,
            organization_slug=payload.organization_slug,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    db.commit()
    return AuthResponse(
        user=_user_public(user),
        organization={
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "is_active": organization.is_active,
        },
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate_user(db, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    membership = get_default_membership(db, user.id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no active organization membership")

    from app.core.security import create_access_token, create_refresh_token

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return AuthResponse(
        user=_user_public(user),
        organization={
            "id": membership.organization.id,
            "name": membership.organization.name,
            "slug": membership.organization.slug,
            "is_active": membership.organization.is_active,
        },
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    try:
        token_payload = decode_token(payload.refresh_token, token_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    user = db.get(User, token_payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    from app.core.security import create_access_token, create_refresh_token

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get("/me", response_model=MeResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeResponse:
    membership = get_default_membership(db, current_user.id)
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superadmin=current_user.is_superadmin,
        organization_id=membership.organization_id if membership else None,
        organization_name=membership.organization.name if membership and membership.organization else None,
    )
