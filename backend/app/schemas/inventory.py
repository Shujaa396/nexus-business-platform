from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class InventoryItemCreate(BaseModel):
    branch_id: UUID
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    reorder_level: Decimal | None = None
    notes: str | None = None


class InventoryAdjust(BaseModel):
    branch_id: UUID
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    direction: str = Field(pattern=r"^(IN|OUT)$")
    notes: str | None = None


class StockOpRequest(BaseModel):
    branch_id: UUID
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    notes: str | None = None


class InventoryItemResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    product_id: UUID
    quantity: Decimal
    reorder_level: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryTransactionResponse(BaseModel):
    id: UUID
    transaction_type: str
    quantity: Decimal
    reference_type: str | None
    reference_id: UUID | None
    notes: str | None
    created_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
