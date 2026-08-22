from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_current_membership, require_role
from app.db.session import get_db
from app.models import InventoryTransaction, InventoryTransfer, WarehouseInventory
from app.schemas.inventory import InventoryTransactionResponse
from app.schemas.pagination import Page
from app.schemas.warehouses import (
    InventoryAdjustmentCreate,
    InventoryReservationCreate,
    InventoryReservationResponse,
    InventoryTransferCreate,
    InventoryTransferResponse,
    WarehouseCreate,
    WarehouseInventoryResponse,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.services import warehouse as warehouse_service
from app.services.audit import log_activity

router = APIRouter(tags=["warehouses"])


def audit(db: Session, membership: Any, action: str, entity_type: str, entity_id: UUID | None, details: str) -> None:
    log_activity(db, organization_id=membership.organization_id, user=membership.user, action=action, entity_type=entity_type, entity_id=entity_id, details=details)


def error(exc: warehouse_service.WarehouseError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.post("/warehouses", response_model=WarehouseResponse, status_code=201)
def create_warehouse(payload: WarehouseCreate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    try:
        warehouse = warehouse_service.create_warehouse(db, membership.organization_id, payload)
        audit(db, membership, "WAREHOUSE_CREATED", "WAREHOUSE", warehouse.id, f"Created warehouse {warehouse.code}")
        db.commit()
        db.refresh(warehouse)
        return warehouse
    except warehouse_service.WarehouseError as exc:
        db.rollback()
        raise error(exc) from exc


@router.get("/warehouses", response_model=list[WarehouseResponse])
def list_warehouses(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None), membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    return warehouse_service.list_warehouses(db, membership.organization_id, page, page_size, q)


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(warehouse_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    try:
        return warehouse_service.get_warehouse(db, membership.organization_id, warehouse_id)
    except warehouse_service.WarehouseError as exc:
        raise error(exc) from exc


@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(warehouse_id: UUID, payload: WarehouseUpdate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    try:
        warehouse = warehouse_service.update_warehouse(db, membership.organization_id, warehouse_id, payload)
        audit(db, membership, "WAREHOUSE_UPDATED", "WAREHOUSE", warehouse.id, f"Updated warehouse {warehouse.code}")
        db.commit()
        db.refresh(warehouse)
        return warehouse
    except warehouse_service.WarehouseError as exc:
        db.rollback()
        raise error(exc) from exc


@router.delete("/warehouses/{warehouse_id}")
def deactivate_warehouse(warehouse_id: UUID, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    try:
        warehouse = warehouse_service.update_warehouse(db, membership.organization_id, warehouse_id, WarehouseUpdate(is_active=False))
        audit(db, membership, "WAREHOUSE_DEACTIVATED", "WAREHOUSE", warehouse.id, f"Deactivated warehouse {warehouse.code}")
        db.commit()
        return {"status": "ok"}
    except warehouse_service.WarehouseError as exc:
        db.rollback()
        raise error(exc) from exc


def inventory_response(item: WarehouseInventory) -> WarehouseInventoryResponse:
    product_cost = item.product.cost_price if item.product is not None else Decimal(0)
    return WarehouseInventoryResponse(
        id=item.id, organization_id=item.organization_id, warehouse_id=item.warehouse_id, product_id=item.product_id,
        quantity=item.quantity, reserved_quantity=item.reserved_quantity, available_quantity=item.available_quantity,
        reorder_level=item.reorder_level, reorder_quantity=item.reorder_quantity,
        inventory_value=item.quantity * product_cost,
    )


@router.get("/inventory/by-warehouse", response_model=list[WarehouseInventoryResponse] | Page[WarehouseInventoryResponse])
def list_warehouse_inventory(warehouse_id: UUID | None = Query(None), product_id: UUID | None = Query(None), low_stock: bool = Query(False), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), paginated: bool = False, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    query = db.query(WarehouseInventory).filter(WarehouseInventory.organization_id == membership.organization_id)
    if warehouse_id:
        query = query.filter(WarehouseInventory.warehouse_id == warehouse_id)
    if product_id:
        query = query.filter(WarehouseInventory.product_id == product_id)
    if low_stock:
        query = query.filter(WarehouseInventory.quantity - WarehouseInventory.reserved_quantity <= WarehouseInventory.reorder_level)
    total = query.count()
    items = [inventory_response(item) for item in query.offset((page - 1) * page_size).limit(page_size).all()]
    if not paginated:
        return items
    total_pages = (total + page_size - 1) // page_size
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


@router.get("/inventory/alerts")
def inventory_alerts(warehouse_id: UUID | None = Query(None), membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    query = db.query(WarehouseInventory).filter(WarehouseInventory.organization_id == membership.organization_id, WarehouseInventory.quantity - WarehouseInventory.reserved_quantity <= WarehouseInventory.reorder_level)
    if warehouse_id:
        query = query.filter(WarehouseInventory.warehouse_id == warehouse_id)
    return [{"warehouse_id": item.warehouse_id, "product_id": item.product_id, "quantity": item.quantity, "reserved_quantity": item.reserved_quantity, "available_quantity": item.available_quantity, "reorder_level": item.reorder_level, "suggested_reorder_quantity": item.reorder_quantity} for item in query.all()]


@router.get("/inventory/valuation")
def inventory_valuation(warehouse_id: UUID | None = Query(None), membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    query = db.query(WarehouseInventory).filter(WarehouseInventory.organization_id == membership.organization_id)
    if warehouse_id:
        query = query.filter(WarehouseInventory.warehouse_id == warehouse_id)
    rows = query.all()
    by_warehouse: dict[str, Decimal] = {}
    total = Decimal(0)
    for item in rows:
        value = item.quantity * (item.product.cost_price if item.product else Decimal(0))
        total += value
        by_warehouse[str(item.warehouse_id)] = by_warehouse.get(str(item.warehouse_id), Decimal(0)) + value
    return {"total_inventory_value": total, "by_warehouse": [{"warehouse_id": key, "inventory_value": value} for key, value in by_warehouse.items()]}


@router.post("/inventory/adjustments", response_model=WarehouseInventoryResponse)
def adjust_inventory(payload: InventoryAdjustmentCreate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    try:
        item = warehouse_service.adjust_inventory(db, membership.organization_id, membership.user, payload)
        audit(db, membership, "WAREHOUSE_INVENTORY_ADJUSTED", "WAREHOUSE_INVENTORY", item.id, f"Adjusted product {item.product_id}: {payload.reason}")
        db.commit()
        db.refresh(item)
        return inventory_response(item)
    except warehouse_service.WarehouseError as exc:
        db.rollback()
        raise error(exc) from exc


@router.get("/inventory/movements", response_model=list[InventoryTransactionResponse] | Page[InventoryTransactionResponse])
def inventory_movements(product_id: UUID | None = Query(None), warehouse_id: UUID | None = Query(None), movement_type: str | None = Query(None), date_from: datetime | None = Query(None), date_to: datetime | None = Query(None), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), paginated: bool = False, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    query = db.query(InventoryTransaction).filter(InventoryTransaction.organization_id == membership.organization_id, InventoryTransaction.warehouse_id.is_not(None))
    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)
    if warehouse_id:
        query = query.filter(InventoryTransaction.warehouse_id == warehouse_id)
    if movement_type:
        query = query.filter(InventoryTransaction.transaction_type == movement_type)
    if date_from:
        query = query.filter(InventoryTransaction.created_at >= date_from)
    if date_to:
        query = query.filter(InventoryTransaction.created_at <= date_to)
    total = query.count()
    items = query.order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    if not paginated:
        return items
    total_pages = (total + page_size - 1) // page_size
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


@router.post("/inventory/transfers", response_model=InventoryTransferResponse, status_code=201)
def create_transfer(payload: InventoryTransferCreate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    try:
        transfer = warehouse_service.create_transfer(db, membership.organization_id, membership.user, payload)
        audit(db, membership, "INVENTORY_TRANSFER_CREATED", "INVENTORY_TRANSFER", transfer.id, "Created inventory transfer")
        db.commit()
        db.refresh(transfer)
        return transfer
    except warehouse_service.WarehouseError as exc:
        db.rollback()
        raise error(exc) from exc


@router.get("/inventory/transfers", response_model=list[InventoryTransferResponse] | Page[InventoryTransferResponse])
def list_transfers(status_filter: str | None = Query(None, alias="status"), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), paginated: bool = False, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    query = db.query(InventoryTransfer).filter(InventoryTransfer.organization_id == membership.organization_id)
    if status_filter:
        query = query.filter(InventoryTransfer.status == status_filter)
    total = query.count()
    items = query.order_by(InventoryTransfer.created_at.desc(), InventoryTransfer.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    if not paginated:
        return items
    total_pages = (total + page_size - 1) // page_size
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_previous": page > 1}


@router.get("/inventory/transfers/{transfer_id}", response_model=InventoryTransferResponse)
def get_transfer(transfer_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    transfer = db.query(InventoryTransfer).options(selectinload(InventoryTransfer.items)).filter(InventoryTransfer.id == transfer_id, InventoryTransfer.organization_id == membership.organization_id).first()
    if transfer is None:
        raise HTTPException(status_code=404, detail="Inventory transfer not found")
    return transfer


def transition_transfer(target: str, action: str):
    def endpoint(transfer_id: UUID, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
        try:
            transfer = warehouse_service.transition_transfer(db, membership.organization_id, transfer_id, target, membership.user)
            audit(db, membership, action, "INVENTORY_TRANSFER", transfer.id, f"Moved transfer to {target}")
            db.commit()
            db.refresh(transfer)
            return transfer
        except warehouse_service.WarehouseError as exc:
            db.rollback()
            raise error(exc) from exc
    return endpoint


router.add_api_route("/inventory/transfers/{transfer_id}/approve", transition_transfer("APPROVED", "INVENTORY_TRANSFER_APPROVED"), methods=["POST"], response_model=InventoryTransferResponse)
router.add_api_route("/inventory/transfers/{transfer_id}/dispatch", transition_transfer("IN_TRANSIT", "INVENTORY_TRANSFER_DISPATCHED"), methods=["POST"], response_model=InventoryTransferResponse)
router.add_api_route("/inventory/transfers/{transfer_id}/receive", transition_transfer("COMPLETED", "INVENTORY_TRANSFER_RECEIVED"), methods=["POST"], response_model=InventoryTransferResponse)
router.add_api_route("/inventory/transfers/{transfer_id}/cancel", transition_transfer("CANCELLED", "INVENTORY_TRANSFER_CANCELLED"), methods=["POST"], response_model=InventoryTransferResponse)


@router.post("/inventory/reservations", response_model=InventoryReservationResponse, status_code=201)
def reserve(payload: InventoryReservationCreate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    try:
        reservation = warehouse_service.reserve_inventory(db, membership.organization_id, membership.user, payload)
        audit(db, membership, "INVENTORY_RESERVED", "INVENTORY_RESERVATION", reservation.id, "Reserved warehouse inventory")
        db.commit()
        db.refresh(reservation)
        return reservation
    except warehouse_service.WarehouseError as exc:
        db.rollback()
        raise error(exc) from exc


@router.post("/inventory/reservations/{reservation_id}/release", response_model=InventoryReservationResponse)
def release(reservation_id: UUID, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    try:
        reservation = warehouse_service.release_reservation(db, membership.organization_id, reservation_id)
        audit(db, membership, "INVENTORY_RESERVATION_RELEASED", "INVENTORY_RESERVATION", reservation.id, "Released warehouse inventory reservation")
        db.commit()
        db.refresh(reservation)
        return reservation
    except warehouse_service.WarehouseError as exc:
        db.rollback()
        raise error(exc) from exc
