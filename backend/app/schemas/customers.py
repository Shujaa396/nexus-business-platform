from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.invoices import InvoiceResponse


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    customer_code: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    billing_address: str | None = None
    shipping_address: str | None = None
    status: str = "ACTIVE"
    notes: str | None = None
    credit_limit: Decimal = Field(default=0, ge=0)
    discount_percent: Decimal = Field(default=0, ge=0, le=100)


class CustomerResponse(BaseModel):
    id: UUID
    organization_id: UUID
    customer_code: str | None
    name: str
    company_name: str | None
    email: str | None
    phone: str | None
    address: str | None
    billing_address: str | None
    shipping_address: str | None
    status: str
    notes: str | None
    credit_limit: Decimal
    discount_percent: Decimal
    user_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerUpdate(BaseModel):
    name: str | None = None
    customer_code: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    billing_address: str | None = None
    shipping_address: str | None = None
    status: str | None = None
    notes: str | None = None
    credit_limit: Decimal | None = Field(default=None, ge=0)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None

    model_config = {"from_attributes": True}


class CustomerAccountCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)


class CustomerContactCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    job_title: str | None = None
    is_primary: bool = False
    is_active: bool = True


class CustomerContactResponse(CustomerContactCreate):
    id: UUID
    organization_id: UUID
    customer_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerAddressCreate(BaseModel):
    address_type: str = Field(pattern="^(BILLING|SHIPPING|OTHER)$")
    label: str | None = None
    line1: str = Field(min_length=1)
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    is_primary: bool = False
    is_active: bool = True


class CustomerAddressResponse(CustomerAddressCreate):
    id: UUID
    organization_id: UUID
    customer_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerPage(BaseModel):
    items: list[CustomerResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class CustomerPaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    order_number: str
    invoice_number: str | None
    amount: Decimal
    payment_method: str
    reference: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerOrderPage(BaseModel):
    items: list
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class CustomerInvoicePage(CustomerOrderPage):
    pass


class CustomerPaymentPage(CustomerOrderPage):
    items: list[CustomerPaymentResponse]


class CustomerContactPage(CustomerOrderPage):
    items: list[CustomerContactResponse]


class CustomerAddressPage(CustomerOrderPage):
    items: list[CustomerAddressResponse]


class CustomerInvoicePortalResponse(BaseModel):
    invoice: InvoiceResponse
    payments: list[CustomerPaymentResponse]
