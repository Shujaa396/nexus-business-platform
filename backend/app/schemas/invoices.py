from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvoiceLineItemResponse(BaseModel):
    id: UUID
    organization_id: UUID
    invoice_id: UUID
    order_item_id: UUID
    product_id: UUID
    product_sku: str
    product_name: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    tax: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    order_id: UUID
    due_date: datetime | None = None
    notes: str | None = None


class InvoiceIssue(BaseModel):
    due_date: datetime | None = None
    notes: str | None = None


class InvoicePayment(BaseModel):
    amount: Decimal
    payment_method: str
    reference: str | None = None


class InvoiceVoid(BaseModel):
    notes: str | None = None


class InvoiceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    order_id: UUID
    branch_id: UUID
    customer_id: UUID | None = None
    invoice_number: str
    order_number: str
    branch_name: str
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    status: str
    issued_date: datetime | None = None
    due_date: datetime | None = None
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    amount_paid: Decimal
    notes: str | None = None
    issued_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    line_items: list[InvoiceLineItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
