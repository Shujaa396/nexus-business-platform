from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Branch, InventoryTransaction, Product, PurchaseOrder, PurchaseOrderItem, Supplier, User
from app.schemas.purchase_orders import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    ReceivePurchaseOrder,
)
from app.services.inventory import stock_in


class ProcurementError(Exception):
    pass


TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"SUBMITTED", "CANCELLED"},
    "SUBMITTED": {"APPROVED", "CANCELLED"},
    "APPROVED": {"PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"},
    "PARTIALLY_RECEIVED": {"RECEIVED"},
    "RECEIVED": set(),
    "CANCELLED": set(),
}


def _get_order(db: Session, organization_id: UUID, purchase_order_id: UUID, *, lock: bool = False) -> PurchaseOrder:
    stmt = select(PurchaseOrder).where(
        PurchaseOrder.id == purchase_order_id,
        PurchaseOrder.organization_id == organization_id,
    )
    if lock:
        stmt = stmt.with_for_update()
    order = db.execute(stmt).scalars().first()
    if order is None:
        raise ProcurementError("Purchase order not found")
    return order


def _validate_supplier_branch(db: Session, organization_id: UUID, supplier_id: UUID, branch_id: UUID) -> None:
    supplier = db.get(Supplier, supplier_id)
    branch = db.get(Branch, branch_id)
    if supplier is None or supplier.organization_id != organization_id or not supplier.is_active:
        raise ProcurementError("Supplier is not available in this organization")
    if branch is None or branch.organization_id != organization_id or not branch.is_active:
        raise ProcurementError("Branch is not available in this organization")


def _validated_items(db: Session, organization_id: UUID, items: Iterable[object]) -> list[tuple[Product, Decimal, Decimal]]:
    validated: list[tuple[Product, Decimal, Decimal]] = []
    seen: set[UUID] = set()
    for item in items:
        product = db.get(Product, item.product_id)
        if product is None or product.organization_id != organization_id or not product.is_active:
            raise ProcurementError("Product is not available in this organization")
        if product.id in seen:
            raise ProcurementError("A product may appear only once on a purchase order")
        seen.add(product.id)
        quantity = Decimal(item.quantity)
        unit_cost = Decimal(item.unit_cost)
        if quantity <= 0 or unit_cost < 0:
            raise ProcurementError("Quantity must be greater than zero and unit cost cannot be negative")
        validated.append((product, quantity, unit_cost))
    if not validated:
        raise ProcurementError("Purchase order must contain at least one item")
    return validated


def _set_totals(order: PurchaseOrder, items: Iterable[PurchaseOrderItem]) -> None:
    subtotal = sum((item.subtotal for item in items), Decimal(0))
    order.subtotal = subtotal
    order.total = subtotal + (order.tax or Decimal(0)) - (order.discount or Decimal(0))
    if order.total < 0:
        raise ProcurementError("Discount cannot exceed the purchase order subtotal plus tax")


def create_purchase_order(
    db: Session,
    organization_id: UUID,
    user: User,
    payload: PurchaseOrderCreate,
) -> PurchaseOrder:
    _validate_supplier_branch(db, organization_id, payload.supplier_id, payload.branch_id)
    validated = _validated_items(db, organization_id, payload.items)
    order = PurchaseOrder(
        organization_id=organization_id,
        supplier_id=payload.supplier_id,
        branch_id=payload.branch_id,
        purchase_order_number="TEMP",
        status="DRAFT",
        order_date=payload.order_date or datetime.now(UTC),
        expected_delivery_date=payload.expected_delivery_date,
        tax=payload.tax,
        discount=payload.discount,
        notes=payload.notes,
        created_by=user.id,
    )
    db.add(order)
    db.flush()
    order.purchase_order_number = f"PO-{order.id.hex[:8].upper()}"
    for product, quantity, unit_cost in validated:
        db.add(
            PurchaseOrderItem(
                purchase_order_id=order.id,
                organization_id=organization_id,
                product_id=product.id,
                quantity=quantity,
                received_quantity=Decimal(0),
                unit_cost=unit_cost,
                subtotal=quantity * unit_cost,
            )
        )
    db.flush()
    _set_totals(order, order.items)
    db.flush()
    return order


def update_purchase_order(
    db: Session,
    organization_id: UUID,
    purchase_order_id: UUID,
    payload: PurchaseOrderUpdate,
) -> PurchaseOrder:
    order = _get_order(db, organization_id, purchase_order_id)
    if order.status != "DRAFT":
        raise ProcurementError("Only DRAFT purchase orders can be modified")
    supplier_id = payload.supplier_id or order.supplier_id
    branch_id = payload.branch_id or order.branch_id
    _validate_supplier_branch(db, organization_id, supplier_id, branch_id)
    if payload.expected_delivery_date and payload.order_date and payload.expected_delivery_date < payload.order_date:
        raise ProcurementError("expected_delivery_date must not be before order_date")
    for field in ("supplier_id", "branch_id", "order_date", "expected_delivery_date", "tax", "discount", "notes"):
        value = getattr(payload, field)
        if value is not None:
            setattr(order, field, value)
    if payload.items is not None:
        validated = _validated_items(db, organization_id, payload.items)
        for item in list(order.items):
            db.delete(item)
        db.flush()
        for product, quantity, unit_cost in validated:
            db.add(
                PurchaseOrderItem(
                    purchase_order_id=order.id,
                    organization_id=organization_id,
                    product_id=product.id,
                    quantity=quantity,
                    received_quantity=Decimal(0),
                    unit_cost=unit_cost,
                    subtotal=quantity * unit_cost,
                )
            )
        db.flush()
        db.expire(order, ["items"])
    _set_totals(order, order.items)
    db.flush()
    return order


def transition_purchase_order(
    db: Session,
    organization_id: UUID,
    purchase_order_id: UUID,
    target_status: str,
) -> PurchaseOrder:
    order = _get_order(db, organization_id, purchase_order_id, lock=True)
    if target_status not in TRANSITIONS.get(order.status, set()):
        raise ProcurementError(f"Cannot transition purchase order from {order.status} to {target_status}")
    order.status = target_status
    db.flush()
    return order


def receive_purchase_order(
    db: Session,
    organization_id: UUID,
    purchase_order_id: UUID,
    user: User,
    payload: ReceivePurchaseOrder,
) -> PurchaseOrder:
    order = _get_order(db, organization_id, purchase_order_id, lock=True)
    if order.status not in {"APPROVED", "PARTIALLY_RECEIVED"}:
        raise ProcurementError("Only APPROVED or PARTIALLY_RECEIVED purchase orders can receive stock")
    duplicate = db.query(InventoryTransaction).filter(
        InventoryTransaction.organization_id == organization_id,
        InventoryTransaction.reference_type == "PURCHASE_ORDER_RECEIPT",
        InventoryTransaction.reference_id == order.id,
        InventoryTransaction.notes == f"Receipt {payload.receipt_reference}",
    ).first()
    if duplicate is not None:
        raise ProcurementError("This receipt reference has already been processed")
    item_map = {item.id: item for item in order.items}
    requested_by_item: dict[UUID, Decimal] = {}
    for received in payload.items:
        item = item_map.get(received.item_id)
        if item is None:
            raise ProcurementError("Purchase order item not found")
        quantity = Decimal(received.quantity)
        requested_by_item[item.id] = requested_by_item.get(item.id, Decimal(0)) + quantity
        remaining = item.quantity - item.received_quantity
        if requested_by_item[item.id] > remaining:
            raise ProcurementError("Received quantity cannot exceed the remaining ordered quantity")
    for item_id, quantity in requested_by_item.items():
        item = item_map[item_id]
        stock_in(
            db,
            organization_id=organization_id,
            branch_id=order.branch_id,
            product_id=item.product_id,
            quantity=quantity,
            user=user,
            notes=f"Receipt {payload.receipt_reference}",
            reference_type="PURCHASE_ORDER_RECEIPT",
            reference_id=order.id,
        )
        item.received_quantity += quantity
    order.status = "RECEIVED" if all(item.received_quantity >= item.quantity for item in order.items) else "PARTIALLY_RECEIVED"
    db.flush()
    return order


def list_purchase_orders(
    db: Session,
    organization_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    supplier_id: UUID | None = None,
    branch_id: UUID | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    purchase_order_number: str | None = None,
) -> list[PurchaseOrder]:
    query = db.query(PurchaseOrder).filter(PurchaseOrder.organization_id == organization_id)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if branch_id:
        query = query.filter(PurchaseOrder.branch_id == branch_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if date_from:
        query = query.filter(PurchaseOrder.order_date >= date_from)
    if date_to:
        query = query.filter(PurchaseOrder.order_date <= date_to)
    if purchase_order_number:
        query = query.filter(PurchaseOrder.purchase_order_number.ilike(f"%{purchase_order_number}%"))
    return query.order_by(PurchaseOrder.order_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
