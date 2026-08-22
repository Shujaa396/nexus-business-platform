from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.schemas.invoices import (
    InvoiceCreate,
    InvoiceIssue,
    InvoicePayment,
    InvoiceResponse,
    InvoiceVoid,
)
from app.schemas.orders import PaymentResponse
from app.schemas.pagination import Page
from app.services import invoices as invoices_service
from app.services import payments as payments_service
from app.services.audit import log_activity

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    membership=Depends(require_role(["admin", "manager"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    user = membership.user
    try:
        invoice = invoices_service.generate_invoice_from_order(
            db,
            organization_id=org_id,
            order_id=payload.order_id,
            user=user,
            due_date=payload.due_date,
            notes=payload.notes,
        )
        log_activity(
            db,
            organization_id=org_id,
            user=user,
            action="INVOICE_CREATED",
            entity_type="INVOICE",
            entity_id=invoice.id,
            details=f"Generated invoice {invoice.invoice_number} (Total: {invoice.total})",
        )
        db.commit()
        db.refresh(invoice)
    except invoices_service.InvoiceValidationError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return invoice


@router.get("", response_model=list[InvoiceResponse] | Page[InvoiceResponse])
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    customer_id: UUID | None = None,
    branch_id: UUID | None = None,
    invoice_number: str | None = None,
    date_from=None,
    date_to=None,
    paginated: bool = False,
    membership=Depends(require_role(["admin", "manager"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    return invoices_service.list_invoices(
        db,
        organization_id=org_id,
        page=page,
        page_size=page_size,
        status=status,
        customer_id=customer_id,
        branch_id=branch_id,
        invoice_number=invoice_number,
        date_from=date_from,
        date_to=date_to,
        paginated=paginated,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: UUID,
    membership=Depends(require_role(["admin", "manager"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    try:
        invoice = invoices_service.get_invoice(db, org_id, invoice_id)
    except invoices_service.InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return invoice


@router.post("/{invoice_id}/issue", response_model=InvoiceResponse)
def issue_invoice(
    invoice_id: UUID,
    payload: InvoiceIssue | None = None,
    membership=Depends(require_role(["admin", "manager"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    user = membership.user
    due_date = payload.due_date if payload else None
    notes = payload.notes if payload else None
    try:
        invoice = invoices_service.issue_invoice(
            db,
            organization_id=org_id,
            invoice_id=invoice_id,
            user=user,
            due_date=due_date,
            notes=notes,
        )
        log_activity(
            db,
            organization_id=org_id,
            user=user,
            action="INVOICE_ISSUED",
            entity_type="INVOICE",
            entity_id=invoice.id,
            details=f"Issued invoice {invoice.invoice_number}",
        )
        db.commit()
        db.refresh(invoice)
    except invoices_service.InvoiceNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except invoices_service.InvoiceStateError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return invoice


@router.post("/{invoice_id}/payments", response_model=PaymentResponse)
def record_invoice_payment(
    invoice_id: UUID,
    payload: InvoicePayment,
    membership=Depends(require_role(["admin", "manager"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    user = membership.user
    try:
        payment = invoices_service.record_invoice_payment(
            db,
            organization_id=org_id,
            invoice_id=invoice_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
            reference=payload.reference,
            user=user,
        )
        log_activity(
            db,
            organization_id=org_id,
            user=user,
            action="PAYMENT_RECORDED",
            entity_type="PAYMENT",
            entity_id=payment.id,
            details=f"Recorded payment of {payment.amount} for invoice {invoice_id} ({payment.payment_method})",
        )
        db.commit()
        db.refresh(payment)
    except invoices_service.InvoiceNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (invoices_service.InvoiceStateError, payments_service.PaymentError) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return payment


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
def void_invoice(
    invoice_id: UUID,
    payload: InvoiceVoid | None = None,
    membership=Depends(require_role(["admin", "manager"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    user = membership.user
    notes = payload.notes if payload else None
    try:
        invoice = invoices_service.void_invoice(
            db,
            organization_id=org_id,
            invoice_id=invoice_id,
            user=user,
            notes=notes,
        )
        log_activity(
            db,
            organization_id=org_id,
            user=user,
            action="INVOICE_VOIDED",
            entity_type="INVOICE",
            entity_id=invoice.id,
            details=f"Voided invoice {invoice.invoice_number}",
        )
        db.commit()
        db.refresh(invoice)
    except invoices_service.InvoiceNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except invoices_service.InvoiceStateError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return invoice
