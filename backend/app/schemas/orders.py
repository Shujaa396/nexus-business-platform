from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = None
    discount: Decimal | None = None
    tax: Decimal | None = None


class OrderCreate(BaseModel):
    branch_id: UUID
    customer_id: UUID | None = None
    items: list[OrderItemCreate]
    notes: str | None = None


class OrderUpdate(BaseModel):
    customer_id: UUID | None = None
    items: list[OrderItemCreate] | None = None
    notes: str | None = None


class OrderStatusHistoryResponse(BaseModel):
    id: UUID
    organization_id: UUID
    order_id: UUID
    old_status: str
    new_status: str
    changed_by: UUID | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderItemResponse(BaseModel):
    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    tax: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_method: str
    reference: str | None = None


class PaymentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    order_id: UUID
    amount: Decimal
    payment_method: str
    reference: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    customer_id: UUID | None
    order_number: str
    status: str
    payment_status: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    notes: str | None
    items: list[OrderItemResponse] = []
    payments: list[PaymentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
