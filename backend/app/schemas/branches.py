from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BranchCreate(BaseModel):
    code: str
    name: str
    address: str | None = None
    phone: str | None = None


class BranchUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class BranchResponse(BaseModel):
    id: UUID
    code: str
    name: str
    address: str | None = None
    phone: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
