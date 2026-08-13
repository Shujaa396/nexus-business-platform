from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    organization_name: str = Field(min_length=1, max_length=255)
    organization_slug: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_superadmin: bool

    model_config = {"from_attributes": True}


class OrganizationSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenPairResponse):
    user: UserPublic
    organization: OrganizationSummary


class MeResponse(UserPublic):
    organization_id: UUID | None = None
    organization_name: str | None = None

    model_config = {"from_attributes": True}
