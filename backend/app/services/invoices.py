from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Branch,
    Customer,
    Invoice,
    InvoiceLineItem,
    Order,
    Payment,
    User,
)
from app.services import payments as payments_service


class InvoiceError(Exception):
    pass


class InvoiceNotFoundError(InvoiceError):
    pass


class InvoiceValidationError(InvoiceError):
    pass


class InvoiceStateError(InvoiceError):
    pass


def generate_invoice_number(db: Session, organization_id: UUID) -> str:
    """Generate a unique invoice number scoped to the tenant/organization."""
    existing_count = db.query(Invoice).filter(Invoice.organization_id == organization_id).count()
    counter = existing_count + 1
    while True:
        candidate = f"INV-{counter:06d}"
        exists = (
            db.query(Invoice)
            .filter(Invoice.organization_id == organization_id, Invoice.invoice_number == candidate)
            .first()
        )
        if not exists:
            return candidate
        counter += 1


def sync_invoice_payment_status(db: Session, invoice: Invoice) -> None:
    """Synchronize invoice amount_paid and status based on order payments."""
    if invoice.status == "VOID":
        return

    completed_payments = (
        db.query(Payment)
        .filter(Payment.order_id == invoice.order_id, Payment.status == "COMPLETED")
        .all()
    )
    paid = sum((p.amount for p in completed_payments), Decimal(0))
    invoice.amount_paid = paid

    if invoice.status != "DRAFT":
        if paid >= invoice.total:
            invoice.status = "PAID"
        elif paid > 0:
            invoice.status = "PARTIAL"
        else:
            invoice.status = "ISSUED"
    db.flush()


def generate_invoice_from_order(
    db: Session,
    organization_id: UUID,
    order_id: UUID,
    user: User,
    due_date: datetime | None = None,
    notes: str | None = None,
) -> Invoice:
    """Generate an invoice from a confirmed order.

    Does not deduct inventory again (inventory was deducted on order confirmation).
    Calculates totals server-side and preserves historical snapshot of line items.
    """
    order = db.get(Order, order_id)
    if order is None or order.organization_id != organization_id:
        raise InvoiceValidationError("Order not found or tenant mismatch")

    if order.status not in ("CONFIRMED", "COMPLETED"):
        raise InvoiceValidationError("Invoice can only be generated for CONFIRMED or COMPLETED orders")

    existing_invoice = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization_id, Invoice.order_id == order_id)
        .first()
    )
    if existing_invoice is not None:
        raise InvoiceValidationError("An invoice has already been generated for this order")

    branch = db.get(Branch, order.branch_id)
    branch_name = branch.name if branch else "Main Branch"

    customer_name = None
    customer_email = None
    customer_phone = None
    if order.customer_id:
        customer = db.get(Customer, order.customer_id)
        if customer:
            customer_name = customer.name
            customer_email = customer.email
            customer_phone = customer.phone

    invoice_number = generate_invoice_number(db, organization_id)

    invoice = Invoice(
        organization_id=organization_id,
        order_id=order.id,
        branch_id=order.branch_id,
        customer_id=order.customer_id,
        invoice_number=invoice_number,
        order_number=order.order_number,
        branch_name=branch_name,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        status="DRAFT",
        due_date=due_date,
        subtotal=Decimal(0),
        discount=Decimal(0),
        tax=Decimal(0),
        total=Decimal(0),
        amount_paid=Decimal(0),
        notes=notes,
        issued_by=user.id,
    )
    db.add(invoice)
    db.flush()

    subtotal = Decimal(0)
    total_discount = Decimal(0)
    total_tax = Decimal(0)

    for item in order.items:
        prod = item.product
        prod_sku = prod.sku if prod else "UNKNOWN"
        prod_name = prod.name if prod else "Product"

        line_subtotal = item.quantity * item.unit_price
        line_total = line_subtotal - item.discount + item.tax

        line_item = InvoiceLineItem(
            organization_id=organization_id,
            invoice_id=invoice.id,
            order_item_id=item.id,
            product_id=item.product_id,
            product_sku=prod_sku,
            product_name=prod_name,
            description=prod_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount=item.discount,
            tax=item.tax,
            line_total=line_total,
        )
        db.add(line_item)

        subtotal += line_subtotal
        total_discount += item.discount
        total_tax += item.tax

    invoice.subtotal = subtotal
    invoice.discount = total_discount
    invoice.tax = total_tax
    invoice.total = subtotal - total_discount + total_tax

    sync_invoice_payment_status(db, invoice)

    db.flush()
    return invoice


def issue_invoice(
    db: Session,
    organization_id: UUID,
    invoice_id: UUID,
    user: User,
    due_date: datetime | None = None,
    notes: str | None = None,
) -> Invoice:
    """Issue a DRAFT invoice to ISSUED (or PARTIAL/PAID if payments exist)."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None or invoice.organization_id != organization_id:
        raise InvoiceNotFoundError("Invoice not found")

    if invoice.status != "DRAFT":
        raise InvoiceStateError(f"Cannot issue invoice with status {invoice.status}")

    invoice.status = "ISSUED"
    invoice.issued_date = datetime.now(UTC)
    invoice.issued_by = user.id
    if due_date:
        invoice.due_date = due_date
    if notes:
        invoice.notes = notes

    sync_invoice_payment_status(db, invoice)

    db.flush()
    return invoice


def record_invoice_payment(
    db: Session,
    organization_id: UUID,
    invoice_id: UUID,
    amount: Decimal,
    payment_method: str,
    reference: str | None,
    user: User,
) -> Payment:
    """Record a payment on an invoice, delegating to the existing order Payment model."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None or invoice.organization_id != organization_id:
        raise InvoiceNotFoundError("Invoice not found")

    if invoice.status in ("DRAFT", "VOID"):
        raise InvoiceStateError(f"Cannot record payment for invoice in {invoice.status} status")

    if invoice.status == "PAID":
        raise InvoiceStateError("Invoice is already fully paid")

    payment = payments_service.create_payment(
        db,
        organization_id=organization_id,
        order_id=invoice.order_id,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        user=user,
    )

    sync_invoice_payment_status(db, invoice)

    db.flush()
    return payment


def void_invoice(
    db: Session,
    organization_id: UUID,
    invoice_id: UUID,
    user: User,
    notes: str | None = None,
) -> Invoice:
    """Void an invoice. Cannot void if already PAID or VOID."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None or invoice.organization_id != organization_id:
        raise InvoiceNotFoundError("Invoice not found")

    if invoice.status in ("PAID", "VOID"):
        raise InvoiceStateError(f"Cannot void invoice in {invoice.status} status")

    invoice.status = "VOID"
    if notes:
        invoice.notes = f"{invoice.notes or ''}\nVoided: {notes}".strip()

    db.flush()
    return invoice


def get_invoice(db: Session, organization_id: UUID, invoice_id: UUID) -> Invoice:
    """Get a single invoice by ID, scoped to organization."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None or invoice.organization_id != organization_id:
        raise InvoiceNotFoundError("Invoice not found")
    return invoice


def list_invoices(
    db: Session,
    organization_id: UUID,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    customer_id: UUID | None = None,
    branch_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    invoice_number: str | None = None,
) -> list[Invoice]:
    """List invoices scoped to organization with optional filtering and pagination."""
    query = select(Invoice).where(Invoice.organization_id == organization_id)

    if status:
        query = query.where(Invoice.status == status)
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    if branch_id:
        query = query.where(Invoice.branch_id == branch_id)
    if invoice_number:
        query = query.where(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    if date_from:
        query = query.where(Invoice.created_at >= date_from)
    if date_to:
        query = query.where(Invoice.created_at <= date_to)

    query = query.order_by(Invoice.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    return list(db.scalars(query).all())
