from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership, require_role
from app.db.session import get_db
from app.models import Order
from app.schemas.invoices import InvoiceResponse
from app.schemas.pagination import Page
from app.schemas.sales_orders import (
    FulfillSalesOrder,
    SalesOrderCreate,
    SalesOrderHistoryResponse,
    SalesOrderResponse,
    SalesOrderUpdate,
)
from app.services import invoices as invoice_service
from app.services import sales as sales_service
from app.services.audit import log_activity

router = APIRouter(prefix="/sales-orders", tags=["sales-orders"])


def _error(exc: sales_service.SalesOrderError) -> HTTPException:
    message = str(exc)
    code = (
        status.HTTP_404_NOT_FOUND if "not found" in message.lower() else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(status_code=code, detail=message)


def _audit(db: Session, membership: Any, action: str, order: Order, details: str) -> None:
    log_activity(
        db,
        organization_id=membership.organization_id,
        user=membership.user,
        action=action,
        entity_type="SALES_ORDER",
        entity_id=order.id,
        details=details,
    )


@router.post("", response_model=SalesOrderResponse, status_code=201)
def create_sales_order(
    payload: SalesOrderCreate,
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service.create_sales_order(
            db, membership.organization_id, membership.user, payload
        )
        _audit(
            db,
            membership,
            "SALES_ORDER_CREATED",
            order,
            f"Created sales order {order.order_number}",
        )
        db.commit()
        db.refresh(order)
        return order
    except sales_service.SalesOrderError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.get("", response_model=list[SalesOrderResponse] | Page[SalesOrderResponse])
def list_sales_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: UUID | None = Query(None),
    warehouse_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    order_number: str | None = Query(None),
    paginated: bool = False,
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be before date_to")
    query = db.query(Order).filter(Order.organization_id == membership.organization_id)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if warehouse_id:
        query = query.filter(Order.warehouse_id == warehouse_id)
    if status_filter:
        if status_filter not in sales_service.TRANSITIONS:
            raise HTTPException(status_code=422, detail="Invalid sales order status")
        query = query.filter(Order.status == status_filter)
    if date_from:
        query = query.filter(Order.created_at >= date_from)
    if date_to:
        query = query.filter(Order.created_at <= date_to)
    if order_number:
        query = query.filter(Order.order_number.ilike(f"%{order_number}%"))
    total = query.count()
    items = (
        query.order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    if not paginated:
        return items
    total_pages = (total + page_size - 1) // page_size
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


@router.get(
    "/customers/{customer_id}/sales-orders",
    response_model=list[SalesOrderResponse] | Page[SalesOrderResponse],
)
def customer_sales_orders(
    customer_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    paginated: bool = False,
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    customer = db.query(Order).filter(
        Order.organization_id == membership.organization_id, Order.customer_id == customer_id
    )
    total = customer.count()
    items = (
        customer.order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    if not paginated:
        return items
    total_pages = (total + page_size - 1) // page_size
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


@router.get("/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(
    order_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)
) -> Any:
    try:
        return sales_service._get_order(db, membership.organization_id, order_id)
    except sales_service.SalesOrderError as exc:
        raise _error(exc) from exc


@router.patch("/{order_id}", response_model=SalesOrderResponse)
def update_sales_order(
    order_id: UUID,
    payload: SalesOrderUpdate,
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service.update_sales_order(db, membership.organization_id, order_id, payload)
        _audit(
            db,
            membership,
            "SALES_ORDER_UPDATED",
            order,
            f"Updated sales order {order.order_number}",
        )
        db.commit()
        db.refresh(order)
        return order
    except sales_service.SalesOrderError as exc:
        db.rollback()
        raise _error(exc) from exc


def _transition(target: str, action: str, roles: list[str] | None = None):
    def endpoint(
        order_id: UUID,
        membership=Depends(require_role(roles or ["admin", "manager"])),
        db: Session = Depends(get_db),
    ) -> SalesOrderResponse:
        try:
            order = sales_service.transition(
                db, membership.organization_id, order_id, target, membership.user
            )
            _audit(db, membership, action, order, f"Moved sales order to {target}")
            db.commit()
            db.refresh(order)
            return order
        except sales_service.SalesOrderError as exc:
            db.rollback()
            raise _error(exc) from exc

    return endpoint


router.add_api_route(
    "/{order_id}/submit",
    _transition("SUBMITTED", "SALES_ORDER_SUBMITTED", ["admin", "manager", "staff"]),
    methods=["POST"],
    response_model=SalesOrderResponse,
)
router.add_api_route(
    "/{order_id}/approve",
    _transition("APPROVED", "SALES_ORDER_APPROVED"),
    methods=["POST"],
    response_model=SalesOrderResponse,
)
router.add_api_route(
    "/{order_id}/confirm",
    _transition("CONFIRMED", "SALES_ORDER_CONFIRMED"),
    methods=["POST"],
    response_model=SalesOrderResponse,
)


@router.post("/{order_id}/reserve", response_model=SalesOrderResponse)
def reserve_sales_order(
    order_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service.reserve_order(
            db, membership.organization_id, order_id, membership.user
        )
        _audit(
            db,
            membership,
            "SALES_ORDER_RESERVED",
            order,
            f"Reserved inventory for {order.order_number}",
        )
        db.commit()
        db.refresh(order)
        return order
    except sales_service.SalesOrderError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/{order_id}/fulfill", response_model=SalesOrderResponse)
def fulfill_sales_order(
    order_id: UUID,
    payload: FulfillSalesOrder,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service.fulfill_order(
            db, membership.organization_id, order_id, membership.user, payload
        )
        _audit(
            db,
            membership,
            "SALES_ORDER_FULFILLED",
            order,
            f"Fulfilled quantities for {order.order_number}",
        )
        db.commit()
        db.refresh(order)
        return order
    except sales_service.SalesOrderError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/{order_id}/cancel", response_model=SalesOrderResponse)
def cancel_sales_order(
    order_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service.cancel_order(
            db, membership.organization_id, order_id, membership.user
        )
        _audit(
            db,
            membership,
            "SALES_ORDER_CANCELLED",
            order,
            f"Cancelled sales order {order.order_number}",
        )
        db.commit()
        db.refresh(order)
        return order
    except sales_service.SalesOrderError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/{order_id}/invoice", response_model=InvoiceResponse)
def invoice_sales_order(
    order_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service._get_order(db, membership.organization_id, order_id)
        if order.status != "FULFILLED":
            raise sales_service.SalesOrderError("Only FULFILLED sales orders can be invoiced")
        invoice = invoice_service.generate_invoice_from_order(
            db, membership.organization_id, order.id, membership.user
        )
        order.status = "INVOICED"
        _audit(
            db,
            membership,
            "SALES_ORDER_INVOICED",
            order,
            f"Generated invoice {invoice.invoice_number}",
        )
        db.commit()
        db.refresh(invoice)
        return invoice
    except (sales_service.SalesOrderError, invoice_service.InvoiceValidationError) as exc:
        db.rollback()
        raise _error(sales_service.SalesOrderError(str(exc))) from exc


@router.get("/{order_id}/history", response_model=list[SalesOrderHistoryResponse])
def sales_order_history(
    order_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)
) -> Any:
    try:
        return sales_service._get_order(db, membership.organization_id, order_id).history
    except sales_service.SalesOrderError as exc:
        raise _error(exc) from exc


@router.post("/{order_id}/paid", response_model=SalesOrderResponse)
def mark_sales_order_paid(
    order_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service.mark_order_paid(
            db, membership.organization_id, order_id, membership.user
        )
        _audit(
            db,
            membership,
            "SALES_ORDER_PAID",
            order,
            f"Marked sales order {order.order_number} as paid",
        )
        db.commit()
        db.refresh(order)
        return order
    except sales_service.SalesOrderError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/{order_id}/complete", response_model=SalesOrderResponse)
def complete_sales_order(
    order_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    try:
        order = sales_service.complete_paid_order(
            db, membership.organization_id, order_id, membership.user
        )
        _audit(
            db,
            membership,
            "SALES_ORDER_COMPLETED",
            order,
            f"Completed paid sales order {order.order_number}",
        )
        db.commit()
        db.refresh(order)
        return order
    except sales_service.SalesOrderError as exc:
        db.rollback()
        raise _error(exc) from exc
