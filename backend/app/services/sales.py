from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Branch,
    Customer,
    InventoryReservation,
    Order,
    OrderItem,
    OrderStatusHistory,
    Product,
    User,
    Warehouse,
)
from app.schemas.sales_orders import FulfillSalesOrder, SalesOrderCreate, SalesOrderUpdate
from app.schemas.warehouses import InventoryReservationCreate
from app.services.warehouse import (
    get_or_create_inventory,
    get_warehouse,
    release_reservation,
    reserve_inventory,
)


class SalesOrderError(Exception):
    pass


TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"SUBMITTED", "CONFIRMED", "CANCELLED"},
    "SUBMITTED": {"APPROVED", "CANCELLED"},
    "APPROVED": {"RESERVED", "CANCELLED"},
    "CONFIRMED": {"RESERVED", "CANCELLED"},
    "RESERVED": {"PARTIALLY_FULFILLED", "FULFILLED", "CANCELLED"},
    "PARTIALLY_FULFILLED": {"FULFILLED", "CANCELLED"},
    "FULFILLED": {"INVOICED", "CANCELLED"},
    "INVOICED": {"PAID", "CANCELLED"},
    "PAID": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def _get_order(db: Session, org_id: UUID, order_id: UUID, lock: bool = False) -> Order:
    stmt = select(Order).options(selectinload(Order.items).selectinload(OrderItem.product)).where(Order.id == order_id, Order.organization_id == org_id)
    if lock:
        stmt = stmt.with_for_update()
    order = db.execute(stmt).scalars().first()
    if order is None:
        raise SalesOrderError("Sales order not found")
    return order


def _validate_context(db: Session, org_id: UUID, payload: SalesOrderCreate | SalesOrderUpdate, existing: Order | None = None) -> tuple[UUID, UUID]:
    customer_id = payload.customer_id if payload.customer_id is not None else (existing.customer_id if existing else None)
    branch_id = payload.branch_id if payload.branch_id is not None else (existing.branch_id if existing else None)
    warehouse_id = payload.warehouse_id if payload.warehouse_id is not None else (existing.warehouse_id if existing else None)
    if customer_id:
        customer = db.get(Customer, customer_id)
        if customer is None or customer.organization_id != org_id or not customer.is_active:
            raise SalesOrderError("Customer is not available in this organization")
    branch = db.get(Branch, branch_id)
    warehouse = db.get(Warehouse, warehouse_id)
    if branch is None or branch.organization_id != org_id or not branch.is_active:
        raise SalesOrderError("Branch is not available in this organization")
    if warehouse is None or warehouse.organization_id != org_id or warehouse.branch_id != branch_id or not warehouse.is_active:
        raise SalesOrderError("Warehouse is not available for this branch")
    return branch_id, warehouse_id


def _build_items(db: Session, org_id: UUID, order_id: UUID, items: list, replace: bool = False) -> tuple[Decimal, Decimal, Decimal]:
    if replace:
        for item in list(db.get(Order, order_id).items):
            db.delete(item)
        db.flush()
    seen: set[UUID] = set()
    subtotal = Decimal(0)
    discount = Decimal(0)
    tax = Decimal(0)
    for payload in items:
        if payload.product_id in seen:
            raise SalesOrderError("A product may appear only once on a sales order")
        seen.add(payload.product_id)
        product = db.get(Product, payload.product_id)
        if product is None or product.organization_id != org_id or not product.is_active:
            raise SalesOrderError("Product is not available in this organization")
        quantity = Decimal(payload.quantity)
        unit_price = Decimal(product.selling_price)
        item_discount = Decimal(payload.discount or 0)
        item_tax = Decimal(payload.tax or 0)
        line_total = quantity * unit_price - item_discount + item_tax
        if line_total < 0:
            raise SalesOrderError("Line total cannot be negative")
        db.add(OrderItem(order_id=order_id, product_id=product.id, quantity=quantity, fulfilled_quantity=Decimal(0), unit_price=unit_price, discount=item_discount, tax=item_tax, line_total=line_total))
        subtotal += quantity * unit_price
        discount += item_discount
        tax += item_tax
    if not seen:
        raise SalesOrderError("Sales order must contain at least one item")
    return subtotal, discount, tax


def create_sales_order(db: Session, org_id: UUID, user: User, payload: SalesOrderCreate) -> Order:
    branch_id, warehouse_id = _validate_context(db, org_id, payload)
    order = Order(organization_id=org_id, customer_id=payload.customer_id, branch_id=branch_id, warehouse_id=warehouse_id, order_number="TEMP", status="DRAFT", payment_status="UNPAID", requested_fulfillment_date=payload.requested_fulfillment_date, notes=payload.notes, created_by=user.id, subtotal=0, discount=0, tax=0, total=0)
    db.add(order)
    db.flush()
    subtotal, discount, tax = _build_items(db, org_id, order.id, payload.items)
    order.order_number = f"SO-{order.id.hex[:8].upper()}"
    order.subtotal, order.discount, order.tax, order.total = subtotal, discount, tax, subtotal - discount + tax
    db.flush()
    return order


def update_sales_order(db: Session, org_id: UUID, order_id: UUID, payload: SalesOrderUpdate) -> Order:
    order = _get_order(db, org_id, order_id)
    if order.status != "DRAFT":
        raise SalesOrderError("Only DRAFT sales orders can be modified")
    _validate_context(db, org_id, payload, order)
    for field in ("customer_id", "branch_id", "warehouse_id", "requested_fulfillment_date", "notes"):
        value = getattr(payload, field)
        if value is not None:
            setattr(order, field, value)
    if payload.items is not None:
        subtotal, discount, tax = _build_items(db, org_id, order.id, payload.items, replace=True)
        order.subtotal, order.discount, order.tax, order.total = subtotal, discount, tax, subtotal - discount + tax
    db.flush()
    return order


def transition(db: Session, org_id: UUID, order_id: UUID, target: str, user: User) -> Order:
    order = _get_order(db, org_id, order_id, lock=True)
    if target not in TRANSITIONS.get(order.status, set()):
        raise SalesOrderError(f"Cannot transition sales order from {order.status} to {target}")
    previous_status = order.status
    order.status = target
    db.add(OrderStatusHistory(organization_id=org_id, order_id=order.id, old_status=previous_status, new_status=target, changed_by=user.id, notes=f"Sales order moved to {target}"))
    db.flush()
    return order


def _transition_loaded_order(db: Session, org_id: UUID, order: Order, target: str, user: User) -> None:
    if target not in TRANSITIONS.get(order.status, set()):
        raise SalesOrderError(f"Cannot transition sales order from {order.status} to {target}")
    previous_status = order.status
    order.status = target
    db.add(OrderStatusHistory(organization_id=org_id, order_id=order.id, old_status=previous_status, new_status=target, changed_by=user.id, notes=f"Sales order moved to {target}"))


def reserve_order(db: Session, org_id: UUID, order_id: UUID, user: User) -> Order:
    order = _get_order(db, org_id, order_id, lock=True)
    if order.status not in {"APPROVED", "CONFIRMED"}:
        raise SalesOrderError("Only APPROVED or CONFIRMED sales orders can be reserved")
    for item in order.items:
        reserve_inventory(db, org_id, user, InventoryReservationCreate(warehouse_id=order.warehouse_id, product_id=item.product_id, quantity=item.quantity, reference_type="SALES_ORDER", reference_id=order.id))
    _transition_loaded_order(db, org_id, order, "RESERVED", user)
    db.flush()
    return order


def fulfill_order(db: Session, org_id: UUID, order_id: UUID, user: User, payload: FulfillSalesOrder) -> Order:
    order = _get_order(db, org_id, order_id, lock=True)
    if order.status not in {"RESERVED", "PARTIALLY_FULFILLED"}:
        raise SalesOrderError("Only RESERVED or PARTIALLY_FULFILLED sales orders can be fulfilled")
    requested: dict[UUID, Decimal] = defaultdict(Decimal)
    item_map = {item.id: item for item in order.items}
    for entry in payload.items:
        if entry.item_id not in item_map:
            raise SalesOrderError("Sales order item not found")
        requested[entry.item_id] += Decimal(entry.quantity)
    warehouse = get_warehouse(db, org_id, order.warehouse_id, lock=True)
    for item_id, quantity in requested.items():
        item = item_map[item_id]
        remaining = item.quantity - item.fulfilled_quantity
        if quantity > remaining:
            raise SalesOrderError("Fulfillment quantity exceeds remaining ordered quantity")
        inventory = get_or_create_inventory(db, org_id, warehouse.id, item.product_id, lock=True)
        if inventory.quantity < quantity or inventory.reserved_quantity < quantity:
            raise SalesOrderError("Insufficient reserved inventory for fulfillment")
        inventory.quantity -= quantity
        inventory.reserved_quantity -= quantity
        item.fulfilled_quantity += quantity
        remaining_to_consume = quantity
        reservations = db.query(InventoryReservation).filter(
            InventoryReservation.organization_id == org_id,
            InventoryReservation.warehouse_id == warehouse.id,
            InventoryReservation.product_id == item.product_id,
            InventoryReservation.reference_type == "SALES_ORDER",
            InventoryReservation.reference_id == order.id,
            InventoryReservation.status == "ACTIVE",
        ).order_by(InventoryReservation.created_at.asc()).with_for_update().all()
        for reservation in reservations:
            consumed = min(reservation.quantity, remaining_to_consume)
            reservation.quantity -= consumed
            remaining_to_consume -= consumed
            if reservation.quantity == 0:
                reservation.status = "CONSUMED"
            if remaining_to_consume == 0:
                break
        if remaining_to_consume > 0:
            raise SalesOrderError("Insufficient active reservation for fulfillment")
        from app.services.warehouse import _movement
        _movement(db, org_id, warehouse, item.product_id, quantity, "SALE", user, order.id, payload.notes)
    target = "FULFILLED" if all(item.fulfilled_quantity >= item.quantity for item in order.items) else "PARTIALLY_FULFILLED"
    _transition_loaded_order(db, org_id, order, target, user)
    db.flush()
    return order


def cancel_order(db: Session, org_id: UUID, order_id: UUID, user: User) -> Order:
    order = _get_order(db, org_id, order_id, lock=True)
    if order.status not in {"DRAFT", "SUBMITTED", "APPROVED", "CONFIRMED", "RESERVED", "PARTIALLY_FULFILLED", "FULFILLED"}:
        raise SalesOrderError("Sales order cannot be cancelled in its current state")
    if order.status in {"RESERVED", "PARTIALLY_FULFILLED", "FULFILLED"}:
        reservations = db.query(InventoryReservation).filter(InventoryReservation.organization_id == org_id, InventoryReservation.reference_type == "SALES_ORDER", InventoryReservation.reference_id == order.id, InventoryReservation.status == "ACTIVE").all()
        for reservation in reservations:
            release_reservation(db, org_id, reservation.id)
    _transition_loaded_order(db, org_id, order, "CANCELLED", user)
    db.flush()
    return order


def mark_order_paid(db: Session, org_id: UUID, order_id: UUID, user: User) -> Order:
    order = _get_order(db, org_id, order_id, lock=True)
    if order.status not in {"INVOICED", "FULFILLED", "PAID"}:
        raise SalesOrderError("Only fulfilled or invoiced sales orders can be marked paid")
    if order.status == "PAID":
        return order
    if order.payment_status != "PAID":
        raise SalesOrderError("Sales order cannot be marked paid before payment is complete")
    previous_status = order.status
    if previous_status != "PAID":
        order.status = "PAID"
        db.add(OrderStatusHistory(organization_id=org_id, order_id=order.id, old_status=previous_status, new_status="PAID", changed_by=user.id, notes="Payment completed"))
    db.flush()
    return order


def complete_paid_order(db: Session, org_id: UUID, order_id: UUID, user: User) -> Order:
    order = _get_order(db, org_id, order_id, lock=True)
    if order.status != "PAID" or order.payment_status != "PAID":
        raise SalesOrderError("Only fully paid sales orders can be completed")
    previous_status = order.status
    order.status = "COMPLETED"
    db.add(OrderStatusHistory(organization_id=org_id, order_id=order.id, old_status=previous_status, new_status="COMPLETED", changed_by=user.id, notes="Sales order completed"))
    db.flush()
    return order


def customer_history(db: Session, org_id: UUID, customer_id: UUID) -> dict:
    orders = db.query(Order).filter(Order.organization_id == org_id, Order.customer_id == customer_id).order_by(Order.created_at.desc()).all()
    if not orders:
        customer = db.get(Customer, customer_id)
        if customer is None or customer.organization_id != org_id:
            raise SalesOrderError("Customer not found")
    return {"total_orders": len(orders), "open_orders": sum(order.status not in {"COMPLETED", "CANCELLED"} for order in orders), "completed_orders": sum(order.status in {"COMPLETED", "PAID"} for order in orders), "total_sales": sum((order.total for order in orders if order.status != "CANCELLED"), Decimal(0)), "recent_orders": orders[:10]}
