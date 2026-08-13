from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None


class CustomerResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    email: str | None
    phone: str | None
    address: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    is_active: bool | None = None

    model_config = {"from_attributes": True}
