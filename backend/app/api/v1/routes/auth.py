from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_user,
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MeResponse,
    OrganizationMembershipResponse,
    OrganizationMembershipsResponse,
    OrganizationSummary,
    RefreshTokenRequest,
    RegisterRequest,
    SelectOrganizationRequest,
    TokenPairResponse,
    UserPublic,
)
from app.services.auth import (
    authenticate_user,
    get_default_membership,
    get_user_membership,
    get_user_memberships,
    register_user,
)

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    membership = get_default_membership(db, user.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active organization membership",
        )

    from app.core.security import create_access_token

    access_token = create_access_token(str(user.id))
    refresh_token = issue_refresh_token(db, user)
    db.commit()

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
        user, refresh_token = rotate_refresh_token(db, payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
    db.commit()
    from app.core.security import create_access_token

    access_token = create_access_token(str(user.id))
    return TokenPairResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    revoke_refresh_token(db, payload.refresh_token)
    db.commit()
    return {"success": True}


@router.get("/me", response_model=MeResponse)
def get_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MeResponse:
    membership = get_default_membership(db, current_user.id)
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superadmin=current_user.is_superadmin,
        organization_id=membership.organization_id if membership else None,
        organization_name=membership.organization.name
        if membership and membership.organization
        else None,
        role_name=membership.role.name if membership and membership.role else None,
    )


@router.get("/organizations", response_model=OrganizationMembershipsResponse)
def list_organizations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> OrganizationMembershipsResponse:
    """List all active organization memberships for the authenticated user."""
    memberships = get_user_memberships(db, current_user.id)
    return OrganizationMembershipsResponse(
        memberships=[
            OrganizationMembershipResponse(
                id=m.id,
                organization=OrganizationSummary(
                    id=m.organization.id,
                    name=m.organization.name,
                    slug=m.organization.slug,
                    is_active=m.organization.is_active,
                ),
                role_name=m.role.name if m.role else None,
                is_active=m.is_active,
            )
            for m in memberships
        ]
    )


@router.post("/organizations/select", response_model=AuthResponse)
def select_organization(
    payload: SelectOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Switch to a different organization."""
    # Verify the user has an active membership in the target organization
    membership = get_user_membership(db, current_user.id, payload.organization_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this organization",
        )

    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    # Create new access token with the selected organization context
    access_token = issue_refresh_token(
        db, current_user
    )  # This creates and persists the refresh token
    from app.core.security import create_access_token

    access_token_new = create_access_token(str(current_user.id))

    db.commit()

    return AuthResponse(
        user=UserPublic(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
            is_superadmin=current_user.is_superadmin,
        ),
        organization=OrganizationSummary(
            id=membership.organization.id,
            name=membership.organization.name,
            slug=membership.organization.slug,
            is_active=membership.organization.is_active,
        ),
        access_token=access_token_new,
        refresh_token=access_token,  # The new refresh token created above
        token_type="bearer",
    )
