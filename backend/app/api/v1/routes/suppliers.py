from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_current_membership, require_role
from app.db.session import get_db
from app.models import Supplier
from app.schemas.suppliers import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services.audit import log_activity

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierResponse)
def create_supplier(
    payload: SupplierCreate,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id

    supplier = Supplier(
        organization_id=org_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        notes=payload.notes,
        is_active=True,
    )
    db.add(supplier)
    db.flush()

    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="SUPPLIER_CREATED",
        entity_type="SUPPLIER",
        entity_id=supplier.id,
        details=f"Created supplier {supplier.name}",
    )
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    qry = db.query(Supplier).filter(Supplier.organization_id == org_id)
    if q:
        search = f"%{q.strip()}%"
        qry = qry.filter(
            or_(
                Supplier.name.ilike(search),
                Supplier.email.ilike(search),
                Supplier.phone.ilike(search),
                Supplier.address.ilike(search),
                Supplier.notes.ilike(search),
            )
        )
    
    items = qry.offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    supplier = db.get(Supplier, supplier_id)
    if supplier is None or supplier.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return supplier


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    supplier = db.get(Supplier, supplier_id)
    if supplier is None or supplier.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    
    db.add(supplier)
    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="SUPPLIER_UPDATED",
        entity_type="SUPPLIER",
        entity_id=supplier.id,
        details=f"Updated supplier {supplier.name}",
    )
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    supplier = db.get(Supplier, supplier_id)
    if supplier is None or supplier.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    supplier.is_active = False
    db.add(supplier)
    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="SUPPLIER_DEACTIVATED",
        entity_type="SUPPLIER",
        entity_id=supplier.id,
        details=f"Deactivated supplier {supplier.name}",
    )
    db.commit()
    return {"status": "ok"}
