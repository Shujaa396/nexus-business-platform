from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership
from app.db.session import get_db
from app.models import InventoryItem, InventoryTransaction
from app.schemas.inventory import (
    InventoryAdjust,
    InventoryItemResponse,
    InventoryTransactionResponse,
    StockOpRequest,
)
from app.services.inventory import (
    InsufficientStockError,
    adjust_stock,
    stock_in,
    stock_out,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/stock-in", response_model=InventoryTransactionResponse)
def post_stock_in(
    payload: StockOpRequest,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            tx = stock_in(
                db,
                organization_id=org_id,
                branch_id=payload.branch_id,
                product_id=payload.product_id,
                quantity=Decimal(payload.quantity),
                user=user,
                notes=payload.notes,
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return tx


@router.post("/stock-out", response_model=InventoryTransactionResponse)
def post_stock_out(
    payload: StockOpRequest,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            tx = stock_out(
                db,
                organization_id=org_id,
                branch_id=payload.branch_id,
                product_id=payload.product_id,
                quantity=Decimal(payload.quantity),
                user=user,
                notes=payload.notes,
            )
    except InsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return tx


@router.post("/adjust", response_model=InventoryTransactionResponse)
def post_adjust(
    payload: InventoryAdjust,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    user = membership.user
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            tx = adjust_stock(
                db,
                organization_id=org_id,
                branch_id=payload.branch_id,
                product_id=payload.product_id,
                quantity=Decimal(payload.quantity),
                direction=payload.direction,
                user=user,
                notes=payload.notes,
            )
    except InsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return tx


@router.get("", response_model=list[InventoryItemResponse])
def list_inventory(
    branch_id: Any | None = Query(None),
    product_id: Any | None = Query(None),
    low_stock: bool = Query(False),
    page: int = Query(1),
    page_size: int = Query(20),
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
):
    org_id = membership.organization_id
    q = db.query(InventoryItem).filter(InventoryItem.organization_id == org_id)
    if branch_id:
        q = q.filter(InventoryItem.branch_id == branch_id)
    if product_id:
        q = q.filter(InventoryItem.product_id == product_id)
    if low_stock:
        q = q.filter(InventoryItem.quantity <= InventoryItem.reorder_level)

    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{inventory_id}", response_model=InventoryItemResponse)
def get_inventory_detail(
    inventory_id: str,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
):
    org_id = membership.organization_id
    item = db.get(InventoryItem, inventory_id)
    if item is None or item.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.get("/{inventory_id}/transactions", response_model=list[InventoryTransactionResponse])
def get_inventory_transactions(
    inventory_id: str,
    transaction_type: str | None = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
):
    org_id = membership.organization_id
    item = db.get(InventoryItem, inventory_id)
    if item is None or item.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    q = db.query(InventoryTransaction).filter(InventoryTransaction.inventory_item_id == inventory_id)
    if transaction_type:
        q = q.filter(InventoryTransaction.transaction_type == transaction_type)
    q = q.order_by(InventoryTransaction.created_at.desc())
    txs = q.offset((page - 1) * page_size).limit(page_size).all()
    return txs
