from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership, require_role
from app.db.session import get_db
from app.models import PurchaseOrder
from app.schemas.purchase_orders import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseOrderItemResponse,
    ReceivePurchaseOrder,
    StatusTransitionResponse,
)
from app.services import procurement as procurement_service
from app.services.audit import log_activity

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def _audit(db: Session, membership: Any, action: str, order: PurchaseOrder, details: str) -> None:
    log_activity(
        db,
        organization_id=membership.organization_id,
        user=membership.user,
        action=action,
        entity_type="PURCHASE_ORDER",
        entity_id=order.id,
        details=details,
    )


def _error(exc: procurement_service.ProcurementError) -> HTTPException:
    if str(exc) == "Purchase order not found":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = procurement_service.create_purchase_order(db, membership.organization_id, membership.user, payload)
        _audit(db, membership, "PURCHASE_ORDER_CREATED", order, f"Created purchase order {order.purchase_order_number}")
        db.commit()
        db.refresh(order)
        return order
    except procurement_service.ProcurementError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.get("", response_model=list[PurchaseOrderResponse])
def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: UUID | None = Query(None),
    branch_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    purchase_order_number: str | None = Query(None),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date_from must be before date_to")
    if status_filter and status_filter not in procurement_service.TRANSITIONS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid purchase order status")
    return procurement_service.list_purchase_orders(
        db,
        membership.organization_id,
        page=page,
        page_size=page_size,
        supplier_id=supplier_id,
        branch_id=branch_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        purchase_order_number=purchase_order_number,
    )


@router.get("/{purchase_order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    purchase_order_id: UUID,
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return procurement_service._get_order(db, membership.organization_id, purchase_order_id)
    except procurement_service.ProcurementError as exc:
        raise _error(exc) from exc


@router.get("/{purchase_order_id}/items", response_model=list[PurchaseOrderItemResponse])
def get_purchase_order_items(
    purchase_order_id: UUID,
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = procurement_service._get_order(db, membership.organization_id, purchase_order_id)
        return order.items
    except procurement_service.ProcurementError as exc:
        raise _error(exc) from exc


@router.patch("/{purchase_order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    purchase_order_id: UUID,
    payload: PurchaseOrderUpdate,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = procurement_service.update_purchase_order(db, membership.organization_id, purchase_order_id, payload)
        _audit(db, membership, "PURCHASE_ORDER_UPDATED", order, f"Updated purchase order {order.purchase_order_number}")
        db.commit()
        db.refresh(order)
        return order
    except procurement_service.ProcurementError as exc:
        db.rollback()
        raise _error(exc) from exc


def _transition_route(target_status: str, action: str):
    def endpoint(
        purchase_order_id: UUID,
        membership=Depends(require_role(["admin", "manager"])),
        db: Session = Depends(get_db),
    ) -> StatusTransitionResponse:
        try:
            order = procurement_service.transition_purchase_order(db, membership.organization_id, purchase_order_id, target_status)
            _audit(db, membership, action, order, f"Moved purchase order {order.purchase_order_number} to {target_status}")
            db.commit()
            db.refresh(order)
            return StatusTransitionResponse(purchase_order=order)
        except procurement_service.ProcurementError as exc:
            db.rollback()
            raise _error(exc) from exc

    return endpoint


router.add_api_route("/{purchase_order_id}/submit", _transition_route("SUBMITTED", "PURCHASE_ORDER_SUBMITTED"), methods=["POST"], response_model=StatusTransitionResponse)
router.add_api_route("/{purchase_order_id}/approve", _transition_route("APPROVED", "PURCHASE_ORDER_APPROVED"), methods=["POST"], response_model=StatusTransitionResponse)
router.add_api_route("/{purchase_order_id}/cancel", _transition_route("CANCELLED", "PURCHASE_ORDER_CANCELLED"), methods=["POST"], response_model=StatusTransitionResponse)


@router.post("/{purchase_order_id}/receive", response_model=PurchaseOrderResponse)
def receive_purchase_order(
    purchase_order_id: UUID,
    payload: ReceivePurchaseOrder,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = procurement_service.receive_purchase_order(
            db,
            membership.organization_id,
            purchase_order_id,
            membership.user,
            payload,
        )
        _audit(db, membership, "PURCHASE_ORDER_STOCK_RECEIVED", order, f"Received stock for {order.purchase_order_number} using {payload.receipt_reference}")
        db.commit()
        db.refresh(order)
        return order
    except procurement_service.ProcurementError as exc:
        db.rollback()
        raise _error(exc) from exc
