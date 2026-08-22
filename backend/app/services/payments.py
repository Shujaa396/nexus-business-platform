from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Invoice, Order, Payment
from app.services.orders import OrderValidationError


class PaymentError(Exception):
    pass


def create_payment(db: Session, organization_id: UUID, order_id: UUID, amount: Decimal, payment_method: str, reference: str | None, user) -> Payment:
    order = db.query(Order).filter(Order.id == order_id, Order.organization_id == organization_id).with_for_update().first()
    if order is None or order.organization_id != organization_id:
        raise OrderValidationError("Order not found or tenant mismatch")
    if order.status not in {"CONFIRMED", "COMPLETED", "FULFILLED", "INVOICED", "PAID"}:
        raise PaymentError(f"Cannot record payment for order in {order.status} status")
    if amount <= 0:
        raise PaymentError("Amount must be positive")
    if reference and db.query(Payment).filter(Payment.organization_id == organization_id, Payment.reference == reference).first():
        raise PaymentError("Payment reference has already been processed")
    paid = sum((p.amount for p in order.payments if p.status == "COMPLETED"), Decimal(0))
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
    paid = sum(
        (p.amount for p in db.query(Payment).filter(Payment.order_id == order.id, Payment.status == "COMPLETED").all()),
        Decimal(0),
    )
    if paid >= order.total:
        order.payment_status = "PAID"
    elif paid > 0:
        order.payment_status = "PARTIAL"
    else:
        order.payment_status = "UNPAID"

    # sync invoice payment status if invoice exists
    invoice = db.scalars(select(Invoice).where(Invoice.order_id == order.id)).first()
    if invoice and invoice.status not in ("VOID", "DRAFT"):
        invoice.amount_paid = paid
        if paid >= invoice.total:
            invoice.status = "PAID"
        elif paid > 0:
            invoice.status = "PARTIAL"
        else:
            invoice.status = "ISSUED"

    if order.payment_status == "PAID" and order.status in {"INVOICED", "FULFILLED"}:
        order.status = "PAID"

    db.flush()
    return payment


def list_payments_for_order(db: Session, organization_id: UUID, order_id: UUID, *, page: int = 1, page_size: int = 50, paginated: bool = False):
    order = db.get(Order, order_id)
    if order is None or order.organization_id != organization_id:
        raise OrderValidationError("Order not found or tenant mismatch")
    query = db.query(Payment).filter(Payment.organization_id == organization_id, Payment.order_id == order_id).order_by(Payment.created_at.desc(), Payment.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    if not paginated:
        return items
    total_pages = (total + page_size - 1) // page_size
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


def refund_payment(db: Session, organization_id: UUID, payment_id: UUID, user) -> Payment:
    payment = db.query(Payment).filter(Payment.id == payment_id, Payment.organization_id == organization_id).with_for_update().first()
    if payment is None:
        raise PaymentError("Payment not found")
    if payment.status == "REFUNDED":
        raise PaymentError("Payment already refunded")
    if payment.status != "COMPLETED":
        raise PaymentError(f"Cannot refund payment in {payment.status} status")
    # perform refund: mark refunded and adjust order payment_status
    payment.status = "REFUNDED"
    order = db.query(Order).filter(Order.id == payment.order_id, Order.organization_id == organization_id).with_for_update().first()
    if order is None:
        raise PaymentError("Order not found for payment")
    paid = sum(
        (p.amount for p in db.query(Payment).filter(Payment.order_id == order.id, Payment.status == "COMPLETED").all()),
        Decimal(0),
    )
    if paid >= order.total:
        order.payment_status = "PAID"
    elif paid > 0:
        order.payment_status = "PARTIAL"
    else:
        order.payment_status = "UNPAID"

    # sync invoice payment status if invoice exists
    invoice = db.scalars(select(Invoice).where(Invoice.order_id == order.id)).first()
    if invoice and invoice.status not in ("VOID", "DRAFT"):
        invoice.amount_paid = paid
        if paid >= invoice.total:
            invoice.status = "PAID"
        elif paid > 0:
            invoice.status = "PARTIAL"
        else:
            invoice.status = "ISSUED"

    db.flush()
    return payment
