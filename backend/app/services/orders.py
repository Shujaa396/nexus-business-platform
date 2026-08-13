from __future__ import annotations

from decimal import Decimal
from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Order,
    OrderItem,
    Payment,
    OrderStatusHistory,
    Product,
    User,
)
from app.services.inventory import stock_out, stock_in, InsufficientStockError


class OrderValidationError(Exception):
    pass


def create_order(db: Session, organization_id: UUID, branch_id: UUID, created_by: UUID, items: Iterable[dict], notes: str | None = None) -> Order:
    # items: list of {product_id, quantity, unit_price, discount?, tax?}
    order = Order(
        organization_id=organization_id,
        branch_id=branch_id,
        order_number="TEMP",
        status="DRAFT",
        payment_status="UNPAID",
        subtotal=Decimal(0),
        discount=Decimal(0),
        tax=Decimal(0),
        total=Decimal(0),
        notes=notes,
        created_by=created_by,
    )
    db.add(order)
    db.flush()

    subtotal = Decimal(0)
    total_discount = Decimal(0)
    total_tax = Decimal(0)

    for it in items:
        product = db.get(Product, it["product_id"])
        if product is None:
            raise OrderValidationError("Product not found")
        if product.organization_id != organization_id:
            raise OrderValidationError("Tenant mismatch for product")
        qty = Decimal(it["quantity"])
        raw_unit = it.get("unit_price")
        unit_price = Decimal(raw_unit if raw_unit is not None else product.selling_price)
        raw_discount = it.get("discount")
        discount = Decimal(raw_discount if raw_discount is not None else 0)
        raw_tax = it.get("tax")
        tax = Decimal(raw_tax if raw_tax is not None else 0)
        line_total = (qty * unit_price) - discount + tax
        oi = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
            discount=discount,
            tax=tax,
            line_total=line_total,
        )
        db.add(oi)
        subtotal += qty * unit_price
        total_discount += discount
        total_tax += tax

    order.subtotal = subtotal
    order.discount = total_discount
    order.tax = total_tax
    order.total = subtotal - total_discount + total_tax

    # generate an order number
    order.order_number = f"ORD-{order.id.hex[:8]}"
    db.flush()
    return order


def confirm_order(db: Session, order_id: UUID, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise OrderValidationError("Order not found")
    if order.status != "DRAFT":
        raise OrderValidationError("Only DRAFT orders can be confirmed")

    # attempt to reserve/stock out items atomically
    try:
        for item in order.items:
            stock_out(
                db,
                organization_id=order.organization_id,
                branch_id=order.branch_id,
                product_id=item.product_id,
                quantity=item.quantity,
                user=user,
                notes=f"Order {order.id} confirm",
            )
    except InsufficientStockError as e:
        raise

    old_status = order.status
    order.status = "CONFIRMED"
    hist = OrderStatusHistory(
        organization_id=order.organization_id,
        order_id=order.id,
        old_status=old_status,
        new_status=order.status,
        changed_by=user.id,
        notes="Confirmed",
    )
    db.add(hist)
    db.flush()
    return order


def cancel_order(db: Session, order_id: UUID, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise OrderValidationError("Order not found")
    if order.status != "CONFIRMED":
        raise OrderValidationError("Only CONFIRMED orders can be cancelled")

    # return stock
    for item in order.items:
        stock_in(
            db,
            organization_id=order.organization_id,
            branch_id=order.branch_id,
            product_id=item.product_id,
            quantity=item.quantity,
            user=user,
            notes=f"Order {order.id} cancel",
        )

    old_status = order.status
    order.status = "CANCELLED"
    hist = OrderStatusHistory(
        organization_id=order.organization_id,
        order_id=order.id,
        old_status=old_status,
        new_status=order.status,
        changed_by=user.id,
        notes="Cancelled",
    )
    db.add(hist)
    db.flush()
    return order


def add_payment(db: Session, organization_id: UUID, order_id: UUID, amount: Decimal, payment_method: str, reference: str | None, user: User) -> Payment:
    order = db.get(Order, order_id)
    if order is None or order.organization_id != organization_id:
        raise OrderValidationError("Order not found or tenant mismatch")

    payment = Payment(
        organization_id=organization_id,
        order_id=order_id,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        status="COMPLETED" if amount >= order.total else "PENDING",
    )
    db.add(payment)
    db.flush()

    # update order payment status
    if payment.amount >= order.total:
        order.payment_status = "PAID"
    else:
        order.payment_status = "PARTIAL"

    db.flush()
    return payment


def list_orders(db: Session, organization_id: UUID, *, page: int = 1, page_size: int = 20, status: str | None = None, payment_status: str | None = None, customer_id: UUID | None = None, branch_id: UUID | None = None, date_from=None, date_to=None, order_number: str | None = None):
    stmt = select(Order).where(Order.organization_id == organization_id)
    if status:
        stmt = stmt.filter(Order.status == status)
    if payment_status:
        stmt = stmt.filter(Order.payment_status == payment_status)
    if customer_id:
        stmt = stmt.filter(Order.customer_id == customer_id)
    if branch_id:
        stmt = stmt.filter(Order.branch_id == branch_id)
    if order_number:
        stmt = stmt.filter(Order.order_number.ilike(f"%{order_number}%"))
    if date_from:
        stmt = stmt.filter(Order.created_at >= date_from)
    if date_to:
        stmt = stmt.filter(Order.created_at <= date_to)
    stmt = stmt.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return db.execute(stmt).scalars().all()


def update_order(db: Session, order_id: UUID, user: User, *, customer_id: UUID | None = None, items: Iterable[dict] | None = None, notes: str | None = None) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise OrderValidationError("Order not found")
    if order.status != "DRAFT":
        raise OrderValidationError("Only DRAFT orders can be modified")

    if customer_id is not None:
        order.customer_id = customer_id
    if notes is not None:
        order.notes = notes

    if items is not None:
        # remove existing items
        for existing in list(order.items):
            db.delete(existing)
        db.flush()
        subtotal = Decimal(0)
        total_discount = Decimal(0)
        total_tax = Decimal(0)
        for it in items:
            product = db.get(Product, it["product_id"])
            if product is None:
                raise OrderValidationError("Product not found")
            if product.organization_id != order.organization_id:
                raise OrderValidationError("Tenant mismatch for product")
            if not product.is_active:
                raise OrderValidationError("Product is not active")
            qty = Decimal(it["quantity"])
            if qty <= 0:
                raise OrderValidationError("Quantity must be > 0")
            raw_unit = it.get("unit_price")
            unit_price = Decimal(raw_unit if raw_unit is not None else product.selling_price)
            raw_discount = it.get("discount")
            discount = Decimal(raw_discount if raw_discount is not None else 0)
            raw_tax = it.get("tax")
            tax = Decimal(raw_tax if raw_tax is not None else 0)
            line_total = (qty * unit_price) - discount + tax
            oi = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                discount=discount,
                tax=tax,
                line_total=line_total,
            )
            db.add(oi)
            subtotal += qty * unit_price
            total_discount += discount
            total_tax += tax

        order.subtotal = subtotal
        order.discount = total_discount
        order.tax = total_tax
        order.total = subtotal - total_discount + total_tax

    db.flush()
    return order


def get_order_history(db: Session, organization_id: UUID, order_id: UUID):
    order = db.get(Order, order_id)
    if order is None or order.organization_id != organization_id:
        raise OrderValidationError("Order not found or tenant mismatch")
    return order.history


def complete_order(db: Session, order_id: UUID, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise OrderValidationError("Order not found")
    if order.status != "CONFIRMED":
        raise OrderValidationError("Only CONFIRMED orders can be completed")
    old_status = order.status
    order.status = "COMPLETED"
    hist = OrderStatusHistory(
        organization_id=order.organization_id,
        order_id=order.id,
        old_status=old_status,
        new_status=order.status,
        changed_by=user.id,
        notes="Completed",
    )
    db.add(hist)
    db.flush()
    return order
