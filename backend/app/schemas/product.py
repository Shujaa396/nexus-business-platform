from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: str | None = None
    unit: str
    cost_price: Decimal
    selling_price: Decimal
    tax_rate: Decimal | None = Field(default=0)
    category_id: UUID | None = None
    supplier_id: UUID | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    unit: str | None = None
    cost_price: Decimal | None = None
    selling_price: Decimal | None = None
    tax_rate: Decimal | None = None
    is_active: bool | None = None
    category_id: UUID | None = None
    supplier_id: UUID | None = None


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    description: str | None
    unit: str
    cost_price: Decimal
    selling_price: Decimal
    tax_rate: Decimal
    category_id: UUID | None
    supplier_id: UUID | None
    is_active: bool

    model_config = {"from_attributes": True}
