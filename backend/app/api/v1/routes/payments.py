from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership
from app.db.session import get_db
from app.services.payments import refund_payment, PaymentError

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/{payment_id}/refund")
def refund_payment_route(
    payment_id: UUID,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    try:
        with db.begin():
            p = refund_payment(db, payment_id, user)
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return p
