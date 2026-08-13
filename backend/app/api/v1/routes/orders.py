from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership
from app.db.session import get_db
from app.schemas.orders import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    PaymentCreate,
    PaymentResponse,
)
from app.services import orders as orders_service
from app.services import payments as payments_service
from app.models import Order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
def create_order(
    payload: OrderCreate,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    user = membership.user
    try:
        with db.begin_nested():
            order = orders_service.create_order(
                db,
                organization_id=org_id,
                branch_id=payload.branch_id,
                created_by=user.id,
                items=[it.model_dump() for it in payload.items],
                notes=payload.notes,
            )
    except orders_service.OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return order


@router.get("", response_model=list[OrderResponse])
def list_orders(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    payment_status: str | None = None,
    customer_id: UUID | None = None,
    branch_id: UUID | None = None,
    date_from=None,
    date_to=None,
    order_number: str | None = None,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    return orders_service.list_orders(
        db,
        org_id,
        page=page,
        page_size=page_size,
        status=status,
        payment_status=payment_status,
        customer_id=customer_id,
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to,
        order_number=order_number,
    )


@router.post("/{order_id}/confirm", response_model=OrderResponse)
def confirm_order(
    order_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    try:
        with db.begin_nested():
            order = orders_service.confirm_order(db, order_id, user)
    except orders_service.OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except orders_service.InsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if order.organization_id != membership.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
    return order


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    try:
        with db.begin_nested():
            order = orders_service.cancel_order(db, order_id, user)
    except orders_service.OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if order.organization_id != membership.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
    return order


@router.post("/{order_id}/payments", response_model=PaymentResponse)
def add_payment(
    order_id: UUID,
    payload: PaymentCreate,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            payment = payments_service.create_payment(
                db=db,
                organization_id=org_id,
                order_id=order_id,
                amount=Decimal(payload.amount),
                payment_method=payload.payment_method,
                reference=payload.reference,
                user=user,
            )
    except orders_service.OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return payment


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_detail(
    order_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    order = db.get(Order, order_id)
    if order is None or order.organization_id != membership.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
def patch_order(
    order_id: UUID,
    payload: OrderUpdate,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    try:
        with db.begin_nested():
            items = [it.model_dump() for it in payload.items] if payload.items is not None else None
            order = orders_service.update_order(db, order_id, user, customer_id=payload.customer_id, items=items, notes=payload.notes)
    except orders_service.OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if order.organization_id != membership.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
    return order


@router.post("/{order_id}/complete", response_model=OrderResponse)
def complete_order(
    order_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    try:
        with db.begin():
            order = orders_service.complete_order(db, order_id, user)
    except orders_service.OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if order.organization_id != membership.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
    return order


@router.get("/{order_id}/history")
def get_order_history(order_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)):
    org_id = membership.organization_id
    try:
        history = orders_service.get_order_history(db, org_id, order_id)
    except orders_service.OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    # return chronologically
    return sorted(history, key=lambda h: h.created_at)


@router.get("/{order_id}/payments", response_model=list[PaymentResponse])
def get_order_payments(order_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)):
    org_id = membership.organization_id
    try:
        payments = payments_service.list_payments_for_order(db, org_id, order_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return payments
