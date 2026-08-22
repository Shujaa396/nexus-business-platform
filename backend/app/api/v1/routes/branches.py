from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership, require_role
from app.db.session import get_db
from app.models import Branch
from app.schemas.branches import BranchCreate, BranchResponse, BranchUpdate

router = APIRouter(prefix="/branches", tags=["branches"])


@router.post("", response_model=BranchResponse)
def create_branch(payload: BranchCreate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    existing = db.query(Branch).filter(Branch.organization_id == org_id, Branch.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Branch code already exists")
    branch = Branch(
        organization_id=org_id,
        code=payload.code,
        name=payload.name,
        address=payload.address,
        phone=payload.phone,
        is_active=True,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.get("", response_model=list[BranchResponse])
def list_branches(page: int = Query(1), page_size: int = Query(100), membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    items = db.query(Branch).filter(Branch.organization_id == org_id).offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    branch = db.get(Branch, branch_id)
    if branch is None or branch.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return branch


@router.patch("/{branch_id}", response_model=BranchResponse)
def update_branch(branch_id: UUID, payload: BranchUpdate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    branch = db.get(Branch, branch_id)
    if branch is None or branch.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if payload.code:
        existing = db.query(Branch).filter(Branch.organization_id == org_id, Branch.code == payload.code, Branch.id != branch_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Branch code already exists")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(branch, k, v)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{branch_id}")
def delete_branch(branch_id: UUID, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    branch = db.get(Branch, branch_id)
    if branch is None or branch.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    branch.is_active = False
    db.add(branch)
    db.commit()
    return {"status": "ok"}
