from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Payment, Order
from app.services.orders import OrderValidationError


class PaymentError(Exception):
    pass


def create_payment(db: Session, organization_id: UUID, order_id: UUID, amount: Decimal, payment_method: str, reference: str | None, user) -> Payment:
    order = db.get(Order, order_id)
    if order is None or order.organization_id != organization_id:
        raise OrderValidationError("Order not found or tenant mismatch")
    if amount <= 0:
        raise PaymentError("Amount must be positive")
    remaining = order.total
    paid = sum((p.amount for p in order.payments), Decimal(0))
    remaining = order.total - paid
    if amount > remaining:
        raise PaymentError("Payment exceeds remaining balance")

    payment = Payment(
        organization_id=organization_id,
        order_id=order_id,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        status="COMPLETED",
    )
    db.add(payment)
    db.flush()

    # update order payment status
    paid = sum((p.amount for p in order.payments), Decimal(0))
    if paid >= order.total:
        order.payment_status = "PAID"
    elif paid > 0:
        order.payment_status = "PARTIAL"
    else:
        order.payment_status = "UNPAID"
    db.flush()
    return payment


def list_payments_for_order(db: Session, organization_id: UUID, order_id: UUID):
    order = db.get(Order, order_id)
    if order is None or order.organization_id != organization_id:
        raise OrderValidationError("Order not found or tenant mismatch")
    return order.payments


def refund_payment(db: Session, payment_id: UUID, user) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise PaymentError("Payment not found")
    if payment.status == "REFUNDED":
        raise PaymentError("Payment already refunded")
    # perform refund: mark refunded and adjust order payment_status
    payment.status = "REFUNDED"
    order = db.get(Order, payment.order_id)
    if order is None:
        raise PaymentError("Order not found for payment")
    paid = sum((p.amount for p in order.payments if p.status != "REFUNDED"), Decimal(0))
    if paid >= order.total:
        order.payment_status = "PAID"
    elif paid > 0:
        order.payment_status = "PARTIAL"
    else:
        order.payment_status = "UNPAID"
    db.flush()
    return payment
