from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Branch,
    InventoryItem,
    InventoryTransaction,
    Product,
    User,
)


class InsufficientStockError(Exception):
    pass


def _assert_same_organization(organization_id: UUID, *objs: Iterable[object]) -> None:
    # placeholder: DB-level checks happen when querying; service ensures ids match
    return None


def find_or_create_inventory_item(db: Session, organization_id: UUID, branch_id: UUID, product_id: UUID) -> InventoryItem:
    stmt = select(InventoryItem).where(
        InventoryItem.organization_id == organization_id,
        InventoryItem.branch_id == branch_id,
        InventoryItem.product_id == product_id,
    )
    item = db.execute(stmt).scalars().first()
    if item:
        return item

    item = InventoryItem(
        organization_id=organization_id,
        branch_id=branch_id,
        product_id=product_id,
        quantity=Decimal(0),
        reorder_level=Decimal(0),
    )
    db.add(item)
    db.flush()
    return item


def _lock_inventory_item(db: Session, item_id: UUID) -> InventoryItem | None:
    stmt = select(InventoryItem).where(InventoryItem.id == item_id).with_for_update()
    return db.execute(stmt).scalars().first()


def stock_in(db: Session, *, organization_id: UUID, branch_id: UUID, product_id: UUID, quantity: Decimal, user: User, notes: str | None = None) -> InventoryTransaction:
    # validate ownership
    product = db.get(Product, product_id)
    branch = db.get(Branch, branch_id)
    if product is None or branch is None:
        raise ValueError("Product or branch not found")
    if product.organization_id != organization_id or branch.organization_id != organization_id:
        raise ValueError("Tenant mismatch")

    item = find_or_create_inventory_item(db, organization_id, branch_id, product_id)
    # lock row
    item_locked = _lock_inventory_item(db, item.id)
    if item_locked is None:
        raise RuntimeError("Inventory item disappeared")

    item_locked.quantity = (item_locked.quantity or Decimal(0)) + quantity

    tx = InventoryTransaction(
        organization_id=organization_id,
        branch_id=branch_id,
        product_id=product_id,
        inventory_item_id=item_locked.id,
        transaction_type="STOCK_IN",
        quantity=quantity,
        notes=notes,
        created_by=user.id,
    )
    db.add(tx)
    db.flush()
    return tx


def stock_out(db: Session, *, organization_id: UUID, branch_id: UUID, product_id: UUID, quantity: Decimal, user: User, notes: str | None = None) -> InventoryTransaction:
    product = db.get(Product, product_id)
    branch = db.get(Branch, branch_id)
    if product is None or branch is None:
        raise ValueError("Product or branch not found")
    if product.organization_id != organization_id or branch.organization_id != organization_id:
        raise ValueError("Tenant mismatch")

    stmt = select(InventoryItem).where(
        InventoryItem.organization_id == organization_id,
        InventoryItem.branch_id == branch_id,
        InventoryItem.product_id == product_id,
    )
    item = db.execute(stmt).scalars().first()
    if item is None:
        raise InsufficientStockError("No stock available")

    item_locked = _lock_inventory_item(db, item.id)
    if item_locked.quantity < quantity:
        raise InsufficientStockError("Insufficient stock")

    item_locked.quantity = item_locked.quantity - quantity

    tx = InventoryTransaction(
        organization_id=organization_id,
        branch_id=branch_id,
        product_id=product_id,
        inventory_item_id=item_locked.id,
        transaction_type="STOCK_OUT",
        quantity=quantity,
        notes=notes,
        created_by=user.id,
    )
    db.add(tx)
    db.flush()
    return tx


def adjust_stock(db: Session, *, organization_id: UUID, branch_id: UUID, product_id: UUID, quantity: Decimal, direction: str, user: User, notes: str | None = None) -> InventoryTransaction:
    if direction not in ("IN", "OUT"):
        raise ValueError("Invalid direction")
    if direction == "IN":
        return stock_in(db, organization_id=organization_id, branch_id=branch_id, product_id=product_id, quantity=quantity, user=user, notes=notes)
    return stock_out(db, organization_id=organization_id, branch_id=branch_id, product_id=product_id, quantity=quantity, user=user, notes=notes)
