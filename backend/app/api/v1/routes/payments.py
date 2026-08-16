from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership
from app.db.session import get_db
from app.models import Payment
from app.schemas.orders import PaymentResponse
from app.services.audit import log_activity
from app.services.payments import PaymentError, refund_payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentResponse])
def list_payments(
    page: int = Query(1),
    page_size: int = Query(50),
    order_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    payment_method: str | None = Query(None),
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    q = db.query(Payment).filter(Payment.organization_id == org_id)
    if order_id:
        q = q.filter(Payment.order_id == order_id)
    if status_filter:
        q = q.filter(Payment.status == status_filter)
    if payment_method:
        q = q.filter(Payment.payment_method == payment_method)
    q = q.order_by(Payment.created_at.desc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment_route(
    payment_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    try:
        with db.begin_nested():
            p = refund_payment(db, payment_id, user)
            log_activity(
                db,
                organization_id=p.organization_id,
                user=user,
                action="PAYMENT_REFUNDED",
                entity_type="PAYMENT",
                entity_id=p.id,
                details=f"Refunded payment {p.id} of amount {p.amount}",
            )
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return p
