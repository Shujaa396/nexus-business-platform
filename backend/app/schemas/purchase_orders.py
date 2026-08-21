from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

PURCHASE_ORDER_STATUSES = (
    "DRAFT",
    "SUBMITTED",
    "APPROVED",
    "PARTIALLY_RECEIVED",
    "RECEIVED",
    "CANCELLED",
)


class PurchaseOrderItemCreate(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    branch_id: UUID
    order_date: datetime | None = None
    expected_delivery_date: datetime | None = None
    tax: Decimal = Field(default=Decimal(0), ge=0)
    discount: Decimal = Field(default=Decimal(0), ge=0)
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_dates(self) -> PurchaseOrderCreate:
        if self.order_date and self.expected_delivery_date and self.expected_delivery_date < self.order_date:
            raise ValueError("expected_delivery_date must not be before order_date")
        return self


class PurchaseOrderUpdate(BaseModel):
    supplier_id: UUID | None = None
    branch_id: UUID | None = None
    order_date: datetime | None = None
    expected_delivery_date: datetime | None = None
    tax: Decimal | None = Field(default=None, ge=0)
    discount: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] | None = Field(default=None, min_length=1, max_length=100)


class PurchaseOrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: Decimal
    received_quantity: Decimal
    unit_cost: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class PurchaseOrderResponse(BaseModel):
    id: UUID
    organization_id: UUID
    supplier_id: UUID
    branch_id: UUID
    purchase_order_number: str
    status: str
    order_date: datetime
    expected_delivery_date: datetime | None
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    notes: str | None
    created_by: UUID | None
    items: list[PurchaseOrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReceiveItem(BaseModel):
    item_id: UUID
    quantity: Decimal = Field(gt=0)


class ReceivePurchaseOrder(BaseModel):
    items: list[ReceiveItem] = Field(min_length=1, max_length=100)
    receipt_reference: str = Field(min_length=1, max_length=120)
    notes: str | None = None


class PurchaseOrderStatusHistoryResponse(BaseModel):
    purchase_order_id: UUID
    previous_status: str
    new_status: str
    changed_at: datetime


class StatusTransitionResponse(BaseModel):
    purchase_order: PurchaseOrderResponse
