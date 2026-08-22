from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Customer,
    CustomerAddress,
    CustomerContact,
    Invoice,
    Order,
    OrderItem,
    Organization,
    Payment,
)


def create_customer(db: Session, organization_id: UUID, *, name: str, customer_code: str | None = None, company_name: str | None = None, email: str | None = None, phone: str | None = None, address: str | None = None, billing_address: str | None = None, shipping_address: str | None = None, status: str = "ACTIVE", notes: str | None = None, credit_limit=0, discount_percent=0) -> Customer:
    org = db.get(Organization, organization_id)
    if org is None:
        raise ValueError("Organization not found")
    if status not in {"ACTIVE", "INACTIVE", "PROSPECT", "BLOCKED"}:
        raise ValueError("Invalid customer status")
    if customer_code and db.query(Customer).filter(Customer.organization_id == organization_id, Customer.customer_code == customer_code).first():
        raise ValueError("Customer code already exists")
    if email and db.query(Customer).filter(Customer.organization_id == organization_id, Customer.email == email.lower().strip()).first():
        raise ValueError("Customer email already exists")
    email = email.lower().strip() if email else None
    cust = Customer(
        organization_id=organization_id,
        customer_code=customer_code or f"CUS-{uuid4().hex[:10].upper()}",
        name=name,
        company_name=company_name,
        email=email,
        phone=phone,
        address=address,
        billing_address=billing_address or address,
        shipping_address=shipping_address or address,
        status=status,
        notes=notes,
        credit_limit=credit_limit,
        discount_percent=discount_percent,
    )
    db.add(cust)
    db.flush()
    return cust


def get_customer(db: Session, organization_id: UUID, customer_id: UUID) -> Customer | None:
    stmt = select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id)
    return db.execute(stmt).scalars().first()


def list_customers(db: Session, organization_id: UUID, *, page: int = 1, page_size: int = 20, q: str | None = None, phone: str | None = None, email: str | None = None, status: str | None = None) -> Iterable[Customer]:
    q_stmt = select(Customer).where(Customer.organization_id == organization_id)
    if q:
        term = f"%{q}%"
        q_stmt = q_stmt.filter(or_(Customer.name.ilike(term), Customer.company_name.ilike(term), Customer.customer_code.ilike(term), Customer.email.ilike(term), Customer.phone.ilike(term)))
    if phone:
        q_stmt = q_stmt.filter(Customer.phone.ilike(f"%{phone}%"))
    if email:
        q_stmt = q_stmt.filter(Customer.email.ilike(f"%{email}%"))
    if status:
        q_stmt = q_stmt.filter(Customer.status == status)

    q_stmt = q_stmt.offset((page - 1) * page_size).limit(page_size)
    return db.execute(q_stmt).scalars().all()


def paginate_customers(db: Session, organization_id: UUID, *, page: int = 1, page_size: int = 20, q: str | None = None, phone: str | None = None, email: str | None = None, status: str | None = None) -> dict:
    base = select(Customer).where(Customer.organization_id == organization_id)
    if q:
        term = f"%{q}%"
        base = base.where(or_(Customer.name.ilike(term), Customer.company_name.ilike(term), Customer.customer_code.ilike(term), Customer.email.ilike(term), Customer.phone.ilike(term)))
    if phone:
        base = base.where(Customer.phone.ilike(f"%{phone}%"))
    if email:
        base = base.where(Customer.email.ilike(f"%{email}%"))
    if status:
        base = base.where(Customer.status == status)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = list(db.scalars(base.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    total_pages = (total + page_size - 1) // page_size
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


def update_customer(db: Session, organization_id: UUID, customer_id: UUID, **fields) -> Customer:
    cust = db.get(Customer, customer_id)
    if cust is None or cust.organization_id != organization_id:
        raise ValueError("Customer not found or tenant mismatch")
    if fields.get("status") is not None and fields["status"] not in {"ACTIVE", "INACTIVE", "PROSPECT", "BLOCKED"}:
        raise ValueError("Invalid customer status")
    if fields.get("email"):
        fields["email"] = fields["email"].lower().strip()
        duplicate = db.query(Customer).filter(Customer.organization_id == organization_id, Customer.email == fields["email"], Customer.id != customer_id).first()
        if duplicate:
            raise ValueError("Customer email already exists")
    if fields.get("customer_code"):
        duplicate = db.query(Customer).filter(Customer.organization_id == organization_id, Customer.customer_code == fields["customer_code"], Customer.id != customer_id).first()
        if duplicate:
            raise ValueError("Customer code already exists")
    for field, value in fields.items():
        if value is not None:
            setattr(cust, field, value)
    if fields.get("status") == "INACTIVE":
        cust.is_active = False
    db.flush()
    return cust


def deactivate_customer(db: Session, organization_id: UUID, customer_id: UUID) -> Customer:
    cust = db.get(Customer, customer_id)
    if cust is None or cust.organization_id != organization_id:
        raise ValueError("Customer not found or tenant mismatch")
    cust.is_active = False
    cust.status = "INACTIVE"
    db.flush()
    return cust


def customer_orders(db: Session, organization_id: UUID, customer_id: UUID) -> list[Order]:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    return list(
        db.scalars(
            select(Order).options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.organization_id == organization_id, Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
        ).all()
    )


def _page(query, db: Session, page: int, page_size: int) -> dict:
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    total_pages = (total + page_size - 1) // page_size
    if total_pages and page > total_pages:
        raise ValueError("Page exceeds available results")
    items = list(db.scalars(query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


def paginate_customer_orders(db: Session, organization_id: UUID, customer_id: UUID, page: int, page_size: int) -> dict:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    return _page(select(Order).where(Order.organization_id == organization_id, Order.customer_id == customer_id), db, page, page_size)


def customer_invoices(db: Session, organization_id: UUID, customer_id: UUID) -> list[Invoice]:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    return list(
        db.scalars(
            select(Invoice).options(selectinload(Invoice.line_items))
            .where(Invoice.organization_id == organization_id, Invoice.customer_id == customer_id)
            .order_by(Invoice.created_at.desc())
        ).all()
    )


def paginate_customer_invoices(db: Session, organization_id: UUID, customer_id: UUID, page: int, page_size: int) -> dict:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    query = select(Invoice).where(Invoice.organization_id == organization_id, Invoice.customer_id == customer_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    total_pages = (total + page_size - 1) // page_size
    if total_pages and page > total_pages:
        raise ValueError("Page exceeds available results")
    return {"items": list(db.scalars(query.order_by(Invoice.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()), "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


def customer_payments(db: Session, organization_id: UUID, customer_id: UUID) -> list[Payment]:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    return list(
        db.scalars(
            select(Payment)
            .join(Order, Payment.order_id == Order.id)
            .where(Payment.organization_id == organization_id, Order.customer_id == customer_id)
            .order_by(Payment.created_at.desc())
        ).all()
    )


def customer_payment_views(db: Session, organization_id: UUID, customer_id: UUID) -> list[dict]:
    payments = customer_payments(db, organization_id, customer_id)
    invoices = {invoice.order_id: invoice.invoice_number for invoice in customer_invoices(db, organization_id, customer_id)}
    return [{"id": payment.id, "order_id": payment.order_id, "order_number": payment.order.order_number, "invoice_number": invoices.get(payment.order_id), "amount": payment.amount, "payment_method": payment.payment_method, "reference": payment.reference, "status": payment.status, "created_at": payment.created_at} for payment in payments]


def _paginate_values(items: list, page: int, page_size: int) -> dict:
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    if total_pages and page > total_pages:
        raise ValueError("Page exceeds available results")
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


def paginate_customer_payments(db: Session, organization_id: UUID, customer_id: UUID, page: int, page_size: int) -> dict:
    return _paginate_values(customer_payment_views(db, organization_id, customer_id), page, page_size)


def paginate_customer_contacts(db: Session, organization_id: UUID, customer_id: UUID, page: int, page_size: int) -> dict:
    return _paginate_values(list_customer_contacts(db, organization_id, customer_id), page, page_size)


def paginate_customer_addresses(db: Session, organization_id: UUID, customer_id: UUID, page: int, page_size: int) -> dict:
    return _paginate_values(list_customer_addresses(db, organization_id, customer_id), page, page_size)


def customer_summary(db: Session, organization_id: UUID, customer_id: UUID) -> dict:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    orders = customer_orders(db, organization_id, customer_id)
    invoices = customer_invoices(db, organization_id, customer_id)
    payments = customer_payments(db, organization_id, customer_id)
    paid_amount = sum((payment.amount for payment in payments if payment.status == "COMPLETED"), Decimal(0))
    invoiced_amount = sum((invoice.total for invoice in invoices if invoice.status != "VOID"), Decimal(0))
    invoice_paid = sum((invoice.amount_paid for invoice in invoices if invoice.status != "VOID"), Decimal(0))
    now = datetime.now(UTC)
    overdue_amount = sum(
        (invoice.total - invoice.amount_paid for invoice in invoices if invoice.status not in {"VOID", "PAID"} and invoice.due_date is not None and invoice.due_date < now),
        Decimal(0),
    )
    return {
        "customer_id": customer_id,
        "order_count": len(orders),
        "invoice_count": len(invoices),
        "payment_count": len(payments),
        "sales_total": sum((order.total for order in orders if order.status != "CANCELLED"), Decimal(0)),
        "invoiced_total": invoiced_amount,
        "paid_total": max(paid_amount, invoice_paid),
        "outstanding_balance": max(invoiced_amount - invoice_paid, Decimal(0)),
        "overdue_amount": overdue_amount,
    }


def _set_primary_contact(db: Session, contact: CustomerContact) -> None:
    if contact.is_primary:
        db.query(CustomerContact).filter(CustomerContact.customer_id == contact.customer_id, CustomerContact.id != contact.id).update({CustomerContact.is_primary: False}, synchronize_session=False)


def _set_primary_address(db: Session, address: CustomerAddress) -> None:
    if address.is_primary:
        db.query(CustomerAddress).filter(CustomerAddress.customer_id == address.customer_id, CustomerAddress.id != address.id, CustomerAddress.address_type == address.address_type).update({CustomerAddress.is_primary: False}, synchronize_session=False)


def list_customer_contacts(db: Session, organization_id: UUID, customer_id: UUID) -> list[CustomerContact]:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    return list(db.scalars(select(CustomerContact).where(CustomerContact.organization_id == organization_id, CustomerContact.customer_id == customer_id).order_by(CustomerContact.is_primary.desc(), CustomerContact.created_at)).all())


def create_customer_contact(db: Session, organization_id: UUID, customer_id: UUID, fields: dict) -> CustomerContact:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    contact = CustomerContact(organization_id=organization_id, customer_id=customer_id, **fields)
    db.add(contact)
    db.flush()
    _set_primary_contact(db, contact)
    return contact


def update_customer_contact(db: Session, organization_id: UUID, customer_id: UUID, contact_id: UUID, fields: dict) -> CustomerContact:
    contact = db.query(CustomerContact).filter(CustomerContact.id == contact_id, CustomerContact.organization_id == organization_id, CustomerContact.customer_id == customer_id).first()
    if contact is None:
        raise ValueError("Customer contact not found")
    for field, value in fields.items():
        setattr(contact, field, value)
    db.flush()
    _set_primary_contact(db, contact)
    return contact


def delete_customer_contact(db: Session, organization_id: UUID, customer_id: UUID, contact_id: UUID) -> None:
    contact = db.query(CustomerContact).filter(CustomerContact.id == contact_id, CustomerContact.organization_id == organization_id, CustomerContact.customer_id == customer_id).first()
    if contact is None:
        raise ValueError("Customer contact not found")
    db.delete(contact)
    db.flush()


def list_customer_addresses(db: Session, organization_id: UUID, customer_id: UUID) -> list[CustomerAddress]:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    return list(db.scalars(select(CustomerAddress).where(CustomerAddress.organization_id == organization_id, CustomerAddress.customer_id == customer_id).order_by(CustomerAddress.address_type, CustomerAddress.is_primary.desc(), CustomerAddress.created_at)).all())


def create_customer_address(db: Session, organization_id: UUID, customer_id: UUID, fields: dict) -> CustomerAddress:
    if get_customer(db, organization_id, customer_id) is None:
        raise ValueError("Customer not found")
    address = CustomerAddress(organization_id=organization_id, customer_id=customer_id, **fields)
    db.add(address)
    db.flush()
    _set_primary_address(db, address)
    return address


def update_customer_address(db: Session, organization_id: UUID, customer_id: UUID, address_id: UUID, fields: dict) -> CustomerAddress:
    address = db.query(CustomerAddress).filter(CustomerAddress.id == address_id, CustomerAddress.organization_id == organization_id, CustomerAddress.customer_id == customer_id).first()
    if address is None:
        raise ValueError("Customer address not found")
    for field, value in fields.items():
        setattr(address, field, value)
    db.flush()
    _set_primary_address(db, address)
    return address


def delete_customer_address(db: Session, organization_id: UUID, customer_id: UUID, address_id: UUID) -> None:
    address = db.query(CustomerAddress).filter(CustomerAddress.id == address_id, CustomerAddress.organization_id == organization_id, CustomerAddress.customer_id == customer_id).first()
    if address is None:
        raise ValueError("Customer address not found")
    db.delete(address)
    db.flush()
