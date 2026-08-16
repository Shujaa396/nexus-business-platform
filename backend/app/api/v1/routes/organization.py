from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_membership,
    hash_password,
    require_admin,
)
from app.db.session import get_db
from app.models import Organization, OrganizationMembership, Role, User
from app.schemas.organization import (
    MemberCreate,
    MemberResponse,
    MemberRoleUpdate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.audit import log_activity

router = APIRouter(prefix="/organization", tags=["organization"])


@router.get("", response_model=OrganizationResponse)
def get_organization_profile(
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    org = db.get(Organization, membership.organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.patch("", response_model=OrganizationResponse)
def update_organization_profile(
    payload: OrganizationUpdate,
    membership=Depends(require_admin),
    db: Session = Depends(get_db),
) -> Any:
    org = db.get(Organization, membership.organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(org, k, v)

    db.add(org)
    db.commit()
    db.refresh(org)

    log_activity(
        db,
        organization_id=org.id,
        user=membership.user,
        action="ORGANIZATION_UPDATED",
        entity_type="ORGANIZATION",
        entity_id=org.id,
        details=f"Updated profile fields: {list(payload.model_dump(exclude_unset=True).keys())}",
    )
    db.commit()

    return org


@router.get("/members", response_model=list[MemberResponse])
def list_organization_members(
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.organization_id == org_id)
        .all()
    )

    result = []
    for m in memberships:
        role_name = m.role.name if m.role else "staff"
        result.append(
            MemberResponse(
                membership_id=m.id,
                user_id=m.user.id,
                email=m.user.email,
                full_name=m.user.full_name,
                role_name=role_name,
                is_active=m.is_active and m.user.is_active,
                joined_at=m.joined_at,
            )
        )
    return result


@router.post("/members", response_model=MemberResponse)
def add_organization_member(
    payload: MemberCreate,
    membership=Depends(require_admin),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    email = payload.email.lower().strip()

    # Check if user already exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name=payload.full_name.strip(),
            password_hash=hash_password(payload.password),
            is_active=True,
            is_superadmin=False,
        )
        db.add(user)
        db.flush()

    # Check existing membership
    existing_mem = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user.id,
        )
        .first()
    )
    if existing_mem and existing_mem.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already an active member of this organization",
        )

    # Get or create requested role in this org
    role_name = payload.role_name.lower().strip()
    role = (
        db.query(Role)
        .filter(Role.organization_id == org_id, Role.name == role_name)
        .first()
    )
    if not role:
        role = Role(
            organization_id=org_id,
            name=role_name,
            description=f"Organization {role_name} role",
            is_system_role=True,
        )
        db.add(role)
        db.flush()

    if existing_mem:
        existing_mem.is_active = True
        existing_mem.role_id = role.id
        mem = existing_mem
    else:
        mem = OrganizationMembership(
            organization_id=org_id,
            user_id=user.id,
            role_id=role.id,
            is_active=True,
        )
        db.add(mem)

    db.commit()
    db.refresh(mem)

    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="MEMBER_ADDED",
        entity_type="MEMBERSHIP",
        entity_id=mem.id,
        details=f"Added user {user.email} with role {role_name}",
    )
    db.commit()

    return MemberResponse(
        membership_id=mem.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role_name=role_name,
        is_active=True,
        joined_at=mem.joined_at,
    )


@router.patch("/members/{user_id}/role", response_model=MemberResponse)
def update_member_role(
    user_id: UUID,
    payload: MemberRoleUpdate,
    membership=Depends(require_admin),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    mem = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user_id,
        )
        .first()
    )
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in organization",
        )

    role_name = payload.role_name.lower().strip()
    role = (
        db.query(Role)
        .filter(Role.organization_id == org_id, Role.name == role_name)
        .first()
    )
    if not role:
        role = Role(
            organization_id=org_id,
            name=role_name,
            description=f"Organization {role_name} role",
            is_system_role=True,
        )
        db.add(role)
        db.flush()

    mem.role_id = role.id
    db.add(mem)
    db.commit()
    db.refresh(mem)

    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="MEMBER_ROLE_UPDATED",
        entity_type="MEMBERSHIP",
        entity_id=mem.id,
        details=f"Updated role of user {mem.user.email} to {role_name}",
    )
    db.commit()

    return MemberResponse(
        membership_id=mem.id,
        user_id=mem.user.id,
        email=mem.user.email,
        full_name=mem.user.full_name,
        role_name=role_name,
        is_active=mem.is_active,
        joined_at=mem.joined_at,
    )


@router.delete("/members/{user_id}")
def deactivate_member(
    user_id: UUID,
    membership=Depends(require_admin),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    if user_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own membership",
        )

    mem = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user_id,
        )
        .first()
    )
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in organization",
        )

    mem.is_active = False
    db.add(mem)
    db.commit()

    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="MEMBER_DEACTIVATED",
        entity_type="MEMBERSHIP",
        entity_id=mem.id,
        details=f"Deactivated membership for {mem.user.email}",
    )
    db.commit()

    return {"status": "ok", "message": "Member deactivated"}
