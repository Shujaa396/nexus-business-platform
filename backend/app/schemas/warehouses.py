from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=80)
    branch_id: UUID
    address: str | None = None
    description: str | None = None


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=80)
    branch_id: UUID | None = None
    address: str | None = None
    description: str | None = None
    is_active: bool | None = None


class WarehouseResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    name: str
    code: str
    address: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WarehouseInventoryResponse(BaseModel):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    product_id: UUID
    quantity: Decimal
    reserved_quantity: Decimal
    available_quantity: Decimal
    reorder_level: Decimal
    reorder_quantity: Decimal
    inventory_value: Decimal


class InventoryAdjustmentCreate(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: Decimal
    reason: str = Field(min_length=1, max_length=120)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_quantity(self) -> InventoryAdjustmentCreate:
        if self.quantity == 0:
            raise ValueError("Adjustment quantity cannot be zero")
        return self


class InventoryTransferItemCreate(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)


class InventoryTransferCreate(BaseModel):
    source_warehouse_id: UUID
    destination_warehouse_id: UUID
    items: list[InventoryTransferItemCreate] = Field(min_length=1, max_length=100)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_warehouses(self) -> InventoryTransferCreate:
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError("Source and destination warehouses must differ")
        return self


class InventoryTransferItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: Decimal

    model_config = {"from_attributes": True}


class InventoryTransferResponse(BaseModel):
    id: UUID
    organization_id: UUID
    source_warehouse_id: UUID
    destination_warehouse_id: UUID
    status: str
    notes: str | None
    created_by: UUID | None
    items: list[InventoryTransferItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryReservationCreate(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    reference_type: str | None = Field(default=None, max_length=80)
    reference_id: UUID | None = None


class InventoryReservationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    product_id: UUID
    quantity: Decimal
    status: str
    reference_type: str | None
    reference_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
