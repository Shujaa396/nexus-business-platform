from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: UUID | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    parent_id: UUID | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
