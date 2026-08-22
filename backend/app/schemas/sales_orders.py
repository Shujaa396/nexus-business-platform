from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

SALES_ORDER_STATUSES = (
    "DRAFT", "SUBMITTED", "APPROVED", "RESERVED", "PARTIALLY_FULFILLED",
    "FULFILLED", "INVOICED", "PAID", "COMPLETED", "CANCELLED",
)


class SalesOrderItemCreate(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    discount: Decimal = Field(default=Decimal(0), ge=0)
    tax: Decimal = Field(default=Decimal(0), ge=0)


class SalesOrderCreate(BaseModel):
    customer_id: UUID | None = None
    branch_id: UUID
    warehouse_id: UUID
    requested_fulfillment_date: datetime | None = None
    notes: str | None = None
    items: list[SalesOrderItemCreate] = Field(min_length=1, max_length=100)


class SalesOrderUpdate(BaseModel):
    customer_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
    requested_fulfillment_date: datetime | None = None
    notes: str | None = None
    items: list[SalesOrderItemCreate] | None = Field(default=None, min_length=1, max_length=100)


class FulfillItem(BaseModel):
    item_id: UUID
    quantity: Decimal = Field(gt=0)


class FulfillSalesOrder(BaseModel):
    items: list[FulfillItem] = Field(min_length=1, max_length=100)
    notes: str | None = None


class SalesOrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: Decimal
    fulfilled_quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    tax: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class SalesOrderResponse(BaseModel):
    id: UUID
    organization_id: UUID
    customer_id: UUID | None
    branch_id: UUID
    warehouse_id: UUID | None
    order_number: str
    status: str
    payment_status: str
    requested_fulfillment_date: datetime | None
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    notes: str | None
    items: list[SalesOrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SalesOrderHistoryResponse(BaseModel):
    id: UUID
    old_status: str
    new_status: str
    changed_by: UUID | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True }
