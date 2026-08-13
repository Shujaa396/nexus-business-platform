from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, Organization


def create_customer(db: Session, organization_id: UUID, *, name: str, email: str | None = None, phone: str | None = None, address: str | None = None, notes: str | None = None) -> Customer:
    org = db.get(Organization, organization_id)
    if org is None:
        raise ValueError("Organization not found")
    cust = Customer(
        organization_id=organization_id,
        name=name,
        email=email,
        phone=phone,
        address=address,
        notes=notes,
    )
    db.add(cust)
    db.flush()
    return cust


def get_customer(db: Session, organization_id: UUID, customer_id: UUID) -> Customer | None:
    stmt = select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id)
    return db.execute(stmt).scalars().first()


def list_customers(db: Session, organization_id: UUID, *, page: int = 1, page_size: int = 20, q: str | None = None, phone: str | None = None, email: str | None = None) -> Iterable[Customer]:
    q_stmt = select(Customer).where(Customer.organization_id == organization_id)
    if q:
        q_stmt = q_stmt.filter(Customer.name.ilike(f"%{q}%"))
    if phone:
        q_stmt = q_stmt.filter(Customer.phone.ilike(f"%{phone}%"))
    if email:
        q_stmt = q_stmt.filter(Customer.email.ilike(f"%{email}%"))

    q_stmt = q_stmt.offset((page - 1) * page_size).limit(page_size)
    return db.execute(q_stmt).scalars().all()


def update_customer(db: Session, organization_id: UUID, customer_id: UUID, *, name: str | None = None, email: str | None = None, phone: str | None = None, address: str | None = None, notes: str | None = None, is_active: bool | None = None) -> Customer:
    cust = db.get(Customer, customer_id)
    if cust is None or cust.organization_id != organization_id:
        raise ValueError("Customer not found or tenant mismatch")
    if name is not None:
        cust.name = name
    if email is not None:
        cust.email = email
    if phone is not None:
        cust.phone = phone
    if address is not None:
        cust.address = address
    if notes is not None:
        cust.notes = notes
    if is_active is not None:
        cust.is_active = is_active
    db.flush()
    return cust


def deactivate_customer(db: Session, organization_id: UUID, customer_id: UUID) -> Customer:
    cust = db.get(Customer, customer_id)
    if cust is None or cust.organization_id != organization_id:
        raise ValueError("Customer not found or tenant mismatch")
    cust.is_active = False
    db.flush()
    return cust
