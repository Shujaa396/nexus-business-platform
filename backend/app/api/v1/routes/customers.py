from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership
from app.db.session import get_db
from app.schemas.customers import CustomerCreate, CustomerResponse
from app.services.customers import (
    create_customer,
    deactivate_customer,
    get_customer,
    list_customers,
    update_customer,
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse)
def post_customer(
    payload: CustomerCreate,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    with db.begin_nested():
        cust = create_customer(
            db,
            organization_id=org_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            notes=payload.notes,
        )
    return cust


@router.get("", response_model=list[CustomerResponse])
def get_customers(
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    return list_customers(db, org_id, page=page, page_size=page_size, q=q, phone=phone, email=email)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer_detail(
    customer_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    cust = get_customer(db, org_id, customer_id)
    if cust is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return cust


@router.patch("/{customer_id}", response_model=CustomerResponse)
def patch_customer(
    customer_id: UUID,
    payload: CustomerCreate,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            cust = update_customer(
                db,
                organization_id=org_id,
                customer_id=customer_id,
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                address=payload.address,
                notes=payload.notes,
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return cust


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            _ = deactivate_customer(db, organization_id=org_id, customer_id=customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"success": True}
