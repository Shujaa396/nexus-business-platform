from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardSummaryResponse(BaseModel):
    total_products: int
    total_customers: int
    total_orders: int
    total_invoices: int
    total_revenue: Decimal
    total_payments: Decimal
    pending_payments: Decimal
    low_stock_product_count: int
    today_sales: Decimal
    today_orders: int
    current_month_revenue: Decimal

    model_config = ConfigDict(from_attributes=True)


class SalesAnalyticsItem(BaseModel):
    period: str
    order_count: int
    revenue: Decimal
    payment_total: Decimal
    invoice_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class SalesAnalyticsResponse(BaseModel):
    preset: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    total_orders: int
    total_revenue: Decimal
    total_payments: Decimal
    total_invoices: Decimal
    breakdown: list[SalesAnalyticsItem] = []

    model_config = ConfigDict(from_attributes=True)


class TopProductItem(BaseModel):
    product_id: UUID
    sku: str
    name: str
    units_sold: Decimal
    total_revenue: Decimal

    model_config = ConfigDict(from_attributes=True)


class LowStockItem(BaseModel):
    inventory_item_id: UUID
    product_id: UUID
    branch_id: UUID
    branch_name: str
    sku: str
    name: str
    quantity: Decimal
    reorder_level: Decimal

    model_config = ConfigDict(from_attributes=True)


class ProductAnalyticsResponse(BaseModel):
    top_selling_products: list[TopProductItem] = []
    highest_revenue_products: list[TopProductItem] = []
    low_stock_products: list[LowStockItem] = []
    total_inventory_value: Decimal

    model_config = ConfigDict(from_attributes=True)


class TopCustomerItem(BaseModel):
    customer_id: UUID
    name: str
    email: str | None = None
    order_count: int
    total_spent: Decimal

    model_config = ConfigDict(from_attributes=True)


class CustomerAnalyticsResponse(BaseModel):
    total_customers: int
    new_customers_in_period: int
    top_customers: list[TopCustomerItem] = []

    model_config = ConfigDict(from_attributes=True)


class BranchAnalyticsItem(BaseModel):
    branch_id: UUID
    code: str
    name: str
    order_count: int
    revenue: Decimal
    inventory_items_count: int
    inventory_value: Decimal

    model_config = ConfigDict(from_attributes=True)


class BranchAnalyticsResponse(BaseModel):
    branches: list[BranchAnalyticsItem] = []

    model_config = ConfigDict(from_attributes=True)
