from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Branch,
    InventoryReservation,
    InventoryTransaction,
    InventoryTransfer,
    InventoryTransferItem,
    Product,
    User,
    Warehouse,
    WarehouseInventory,
)
from app.schemas.warehouses import (
    InventoryAdjustmentCreate,
    InventoryReservationCreate,
    InventoryTransferCreate,
    WarehouseCreate,
    WarehouseUpdate,
)


class WarehouseError(Exception):
    pass


TRANSFER_TRANSITIONS = {
    "DRAFT": {"REQUESTED", "CANCELLED"},
    "REQUESTED": {"APPROVED", "CANCELLED"},
    "APPROVED": {"IN_TRANSIT", "CANCELLED"},
    "IN_TRANSIT": {"COMPLETED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def get_warehouse(db: Session, organization_id: UUID, warehouse_id: UUID, lock: bool = False) -> Warehouse:
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.organization_id == organization_id)
    if lock:
        stmt = stmt.with_for_update()
    warehouse = db.execute(stmt).scalars().first()
    if warehouse is None:
        raise WarehouseError("Warehouse not found")
    return warehouse


def validate_branch(db: Session, organization_id: UUID, branch_id: UUID) -> Branch:
    branch = db.get(Branch, branch_id)
    if branch is None or branch.organization_id != organization_id or not branch.is_active:
        raise WarehouseError("Branch is not available in this organization")
    return branch


def create_warehouse(db: Session, organization_id: UUID, payload: WarehouseCreate) -> Warehouse:
    validate_branch(db, organization_id, payload.branch_id)
    exists = db.query(Warehouse).filter(Warehouse.organization_id == organization_id, Warehouse.code == payload.code).first()
    if exists:
        raise WarehouseError("Warehouse code already exists")
    warehouse = Warehouse(organization_id=organization_id, **payload.model_dump())
    db.add(warehouse)
    db.flush()
    return warehouse


def update_warehouse(db: Session, organization_id: UUID, warehouse_id: UUID, payload: WarehouseUpdate) -> Warehouse:
    warehouse = get_warehouse(db, organization_id, warehouse_id)
    values = payload.model_dump(exclude_unset=True)
    if "branch_id" in values:
        validate_branch(db, organization_id, values["branch_id"])
    if "code" in values and values["code"] != warehouse.code:
        exists = db.query(Warehouse).filter(Warehouse.organization_id == organization_id, Warehouse.code == values["code"], Warehouse.id != warehouse_id).first()
        if exists:
            raise WarehouseError("Warehouse code already exists")
    if values.get("is_active") is False and db.query(WarehouseInventory).filter(WarehouseInventory.warehouse_id == warehouse_id, WarehouseInventory.quantity > 0).first():
        raise WarehouseError("Warehouse with stock cannot be deactivated")
    for field, value in values.items():
        setattr(warehouse, field, value)
    db.flush()
    return warehouse


def list_warehouses(db: Session, organization_id: UUID, page: int, page_size: int, query: str | None) -> list[Warehouse]:
    stmt = db.query(Warehouse).filter(Warehouse.organization_id == organization_id)
    if query:
        pattern = f"%{query.strip()}%"
        stmt = stmt.filter((Warehouse.name.ilike(pattern)) | (Warehouse.code.ilike(pattern)))
    return stmt.order_by(Warehouse.name.asc()).offset((page - 1) * page_size).limit(page_size).all()


def get_or_create_inventory(db: Session, organization_id: UUID, warehouse_id: UUID, product_id: UUID, lock: bool = False) -> WarehouseInventory:
    stmt = select(WarehouseInventory).where(
        WarehouseInventory.organization_id == organization_id,
        WarehouseInventory.warehouse_id == warehouse_id,
        WarehouseInventory.product_id == product_id,
    )
    if lock:
        stmt = stmt.with_for_update()
    inventory = db.execute(stmt).scalars().first()
    if inventory:
        return inventory
    product = db.get(Product, product_id)
    if product is None or product.organization_id != organization_id or not product.is_active:
        raise WarehouseError("Product is not available in this organization")
    inventory = WarehouseInventory(organization_id=organization_id, warehouse_id=warehouse_id, product_id=product_id)
    db.add(inventory)
    db.flush()
    return inventory


def _movement(db: Session, organization_id: UUID, warehouse: Warehouse, product_id: UUID, quantity: Decimal, movement_type: str, user: User, reference_id: UUID | None = None, notes: str | None = None, reference_type: str = "WAREHOUSE") -> InventoryTransaction:
    movement = InventoryTransaction(
        organization_id=organization_id,
        branch_id=warehouse.branch_id,
        warehouse_id=warehouse.id,
        product_id=product_id,
        inventory_item_id=get_or_create_legacy_inventory(db, organization_id, warehouse.branch_id, product_id).id,
        transaction_type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        created_by=user.id,
    )
    db.add(movement)
    return movement


def get_or_create_legacy_inventory(db: Session, organization_id: UUID, branch_id: UUID, product_id: UUID):
    from app.services.inventory import find_or_create_inventory_item
    return find_or_create_inventory_item(db, organization_id, branch_id, product_id)


def adjust_inventory(db: Session, organization_id: UUID, user: User, payload: InventoryAdjustmentCreate) -> WarehouseInventory:
    warehouse = get_warehouse(db, organization_id, payload.warehouse_id, lock=True)
    inventory = get_or_create_inventory(db, organization_id, warehouse.id, payload.product_id, lock=True)
    quantity = Decimal(payload.quantity)
    if quantity < 0 and inventory.quantity + quantity < inventory.reserved_quantity:
        raise WarehouseError("Adjustment would make available stock negative")
    inventory.quantity += quantity
    _movement(db, organization_id, warehouse, payload.product_id, abs(quantity), "ADJUSTMENT", user, notes=f"{payload.reason}: {payload.notes or ''}")
    db.flush()
    return inventory


def create_transfer(db: Session, organization_id: UUID, user: User, payload: InventoryTransferCreate) -> InventoryTransfer:
    if payload.source_warehouse_id == payload.destination_warehouse_id:
        raise WarehouseError("Source and destination warehouses must be different")
    source = get_warehouse(db, organization_id, payload.source_warehouse_id)
    destination = get_warehouse(db, organization_id, payload.destination_warehouse_id)
    if not source.is_active or not destination.is_active:
        raise WarehouseError("Both warehouses must be active")
    transfer = InventoryTransfer(organization_id=organization_id, source_warehouse_id=source.id, destination_warehouse_id=destination.id, status="REQUESTED", notes=payload.notes, created_by=user.id)
    db.add(transfer)
    db.flush()
    seen: set[UUID] = set()
    for item in payload.items:
        if item.product_id in seen:
            raise WarehouseError("A product may appear only once on a transfer")
        seen.add(item.product_id)
        product = db.get(Product, item.product_id)
        if product is None or product.organization_id != organization_id or not product.is_active:
            raise WarehouseError("Product is not available in this organization")
        db.add(InventoryTransferItem(transfer_id=transfer.id, organization_id=organization_id, product_id=item.product_id, quantity=item.quantity))
    db.flush()
    return transfer


def transition_transfer(db: Session, organization_id: UUID, transfer_id: UUID, target: str, user: User) -> InventoryTransfer:
    transfer = db.query(InventoryTransfer).filter(InventoryTransfer.id == transfer_id, InventoryTransfer.organization_id == organization_id).with_for_update().first()
    if transfer is None:
        raise WarehouseError("Inventory transfer not found")
    if target not in TRANSFER_TRANSITIONS.get(transfer.status, set()):
        raise WarehouseError(f"Cannot transition transfer from {transfer.status} to {target}")
    if target == "IN_TRANSIT":
        source = get_warehouse(db, organization_id, transfer.source_warehouse_id, lock=True)
        for item in transfer.items:
            inventory = get_or_create_inventory(db, organization_id, source.id, item.product_id, lock=True)
            if inventory.available_quantity < item.quantity:
                raise WarehouseError("Insufficient available stock for transfer")
            inventory.quantity -= item.quantity
            _movement(db, organization_id, source, item.product_id, item.quantity, "TRANSFER_OUT", user, transfer.id, "Transfer dispatched")
    if target == "COMPLETED":
        destination = get_warehouse(db, organization_id, transfer.destination_warehouse_id, lock=True)
        for item in transfer.items:
            inventory = get_or_create_inventory(db, organization_id, destination.id, item.product_id, lock=True)
            inventory.quantity += item.quantity
            _movement(db, organization_id, destination, item.product_id, item.quantity, "TRANSFER_IN", user, transfer.id, "Transfer received")
    transfer.status = target
    db.flush()
    return transfer


def reserve_inventory(db: Session, organization_id: UUID, user: User, payload: InventoryReservationCreate) -> InventoryReservation:
    if payload.reference_type and payload.reference_id:
        existing = db.query(InventoryReservation).filter(
            InventoryReservation.organization_id == organization_id,
            InventoryReservation.warehouse_id == payload.warehouse_id,
            InventoryReservation.product_id == payload.product_id,
            InventoryReservation.reference_type == payload.reference_type,
            InventoryReservation.reference_id == payload.reference_id,
            InventoryReservation.status == "ACTIVE",
        ).first()
        if existing:
            return existing
    warehouse = get_warehouse(db, organization_id, payload.warehouse_id, lock=True)
    inventory = get_or_create_inventory(db, organization_id, warehouse.id, payload.product_id, lock=True)
    if inventory.available_quantity < payload.quantity:
        raise WarehouseError("Insufficient available stock to reserve")
    inventory.reserved_quantity += payload.quantity
    reservation = InventoryReservation(organization_id=organization_id, warehouse_id=warehouse.id, product_id=payload.product_id, quantity=payload.quantity, reference_type=payload.reference_type, reference_id=payload.reference_id, created_by=user.id)
    db.add(reservation)
    db.flush()
    return reservation


def release_reservation(db: Session, organization_id: UUID, reservation_id: UUID, status: str = "RELEASED") -> InventoryReservation:
    reservation = db.query(InventoryReservation).filter(InventoryReservation.id == reservation_id, InventoryReservation.organization_id == organization_id).with_for_update().first()
    if reservation is None:
        raise WarehouseError("Reservation not found")
    if reservation.status != "ACTIVE":
        raise WarehouseError("Reservation is no longer active")
    inventory = get_or_create_inventory(db, organization_id, reservation.warehouse_id, reservation.product_id, lock=True)
    inventory.reserved_quantity -= reservation.quantity
    reservation.status = status
    db.flush()
    return reservation
