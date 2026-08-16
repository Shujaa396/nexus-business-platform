from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class OrganizationUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    tax_number: str | None = None
    currency: str | None = None


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    email: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class MemberCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role_name: str = "staff"  # "admin" | "manager" | "staff"


class MemberRoleUpdate(BaseModel):
    role_name: str  # "admin" | "manager" | "staff"


class MemberResponse(BaseModel):
    membership_id: UUID
    user_id: UUID
    email: str
    full_name: str
    role_name: str
    is_active: bool
    joined_at: datetime

    model_config = {"from_attributes": True}
