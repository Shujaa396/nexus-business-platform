from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models import Payment
from app.schemas.orders import PaymentResponse
from app.schemas.pagination import Page
from app.services.audit import log_activity
from app.services.payments import PaymentError, refund_payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentResponse] | Page[PaymentResponse])
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    order_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    payment_method: str | None = Query(None),
    paginated: bool = False,
    membership=Depends(require_role(["admin", "manager", "staff"])),  # noqa: B008
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
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    if not paginated:
        return items
    total_pages = (total + page_size - 1) // page_size
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment_route(
    payment_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    try:
        with db.begin_nested():
            p = refund_payment(db, membership.organization_id, payment_id, user)
            log_activity(
                db,
                organization_id=p.organization_id,
                user=user,
                action="PAYMENT_REFUNDED",
                entity_type="PAYMENT",
                entity_id=p.id,
                details=f"Refunded payment {p.id} of amount {p.amount}",
            )
            db.commit()
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return p
