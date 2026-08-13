from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any
from uuid import UUID

from app.db.session import get_db
from app.core.security import get_current_membership
from app.models import Category
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=ProductResponse)
def create_category(payload: dict, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    name = payload.get("name")
    parent_id = payload.get("parent_id")
    if parent_id:
        parent = db.get(Category, parent_id)
        if parent is None or parent.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent category")
    category = Category(organization_id=org_id, name=name, parent_id=parent_id, is_active=True)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[ProductResponse])
def list_categories(page: int = Query(1), page_size: int = Query(20), membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    items = db.query(Category).filter(Category.organization_id == org_id).offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{category_id}")
def get_category(category_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    category = db.get(Category, category_id)
    if category is None or category.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return category


@router.patch("/{category_id}")
def update_category(category_id: UUID, payload: dict, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    category = db.get(Category, category_id)
    if category is None or category.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if "parent_id" in payload and payload["parent_id"]:
        parent = db.get(Category, payload["parent_id"])
        if parent is None or parent.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent category")
    for k, v in payload.items():
        setattr(category, k, v)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}")
def delete_category(category_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    category = db.get(Category, category_id)
    if category is None or category.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    category.is_active = False
    db.add(category)
    db.commit()
    return {"status": "ok"}
