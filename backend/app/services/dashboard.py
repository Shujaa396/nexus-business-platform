from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Branch,
    Customer,
    InventoryItem,
    Invoice,
    Order,
    OrderItem,
    Payment,
    Product,
)
from app.schemas.dashboard import (
    BranchAnalyticsItem,
    BranchAnalyticsResponse,
    CustomerAnalyticsResponse,
    DashboardSummaryResponse,
    LowStockItem,
    ProductAnalyticsResponse,
    SalesAnalyticsItem,
    SalesAnalyticsResponse,
    TopCustomerItem,
    TopProductItem,
)


def parse_date_range(
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> tuple[datetime, datetime, str]:
    """Calculate normalized UTC start and end timestamps based on preset or explicit dates."""
    now = datetime.now(UTC)
    if preset == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        effective_preset = "today"
    elif preset == "this_week":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        effective_preset = "this_week"
    elif preset == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
        effective_preset = "this_month"
    elif start_date or end_date:
        start = start_date if start_date else (now - timedelta(days=30))
        end = end_date if end_date else now
        effective_preset = "custom"
    else:
        # Default to last 30 days
        start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        effective_preset = "this_month"

    return start, end, effective_preset


def get_dashboard_summary(db: Session, organization_id: UUID) -> DashboardSummaryResponse:
    """Retrieve top-level summary metrics for the business dashboard."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_products = (
        db.scalar(
            select(func.count(Product.id)).where(Product.organization_id == organization_id)
        )
        or 0
    )

    total_customers = (
        db.scalar(
            select(func.count(Customer.id)).where(Customer.organization_id == organization_id)
        )
        or 0
    )

    total_orders = (
        db.scalar(
            select(func.count(Order.id)).where(Order.organization_id == organization_id)
        )
        or 0
    )

    total_invoices = (
        db.scalar(
            select(func.count(Invoice.id)).where(Invoice.organization_id == organization_id)
        )
        or 0
    )

    # Total revenue from confirmed or completed orders
    total_revenue = (
        db.scalar(
            select(func.coalesce(func.sum(Order.total), Decimal(0))).where(
                Order.organization_id == organization_id,
                Order.status.in_(["CONFIRMED", "COMPLETED"]),
            )
        )
        or Decimal(0)
    )

    # Total completed payments
    total_payments = (
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), Decimal(0))).where(
                Payment.organization_id == organization_id,
                Payment.status == "COMPLETED",
            )
        )
        or Decimal(0)
    )

    pending_payments = max(Decimal(0), total_revenue - total_payments)

    # Low stock product count
    low_stock_product_count = (
        db.scalar(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.organization_id == organization_id,
                InventoryItem.quantity <= InventoryItem.reorder_level,
            )
        )
        or 0
    )

    # Today's sales & orders
    today_sales = (
        db.scalar(
            select(func.coalesce(func.sum(Order.total), Decimal(0))).where(
                Order.organization_id == organization_id,
                Order.status.in_(["CONFIRMED", "COMPLETED"]),
                Order.created_at >= today_start,
            )
        )
        or Decimal(0)
    )

    today_orders = (
        db.scalar(
            select(func.count(Order.id)).where(
                Order.organization_id == organization_id,
                Order.created_at >= today_start,
            )
        )
        or 0
    )

    # Current month revenue
    current_month_revenue = (
        db.scalar(
            select(func.coalesce(func.sum(Order.total), Decimal(0))).where(
                Order.organization_id == organization_id,
                Order.status.in_(["CONFIRMED", "COMPLETED"]),
                Order.created_at >= month_start,
            )
        )
        or Decimal(0)
    )

    return DashboardSummaryResponse(
        total_products=total_products,
        total_customers=total_customers,
        total_orders=total_orders,
        total_invoices=total_invoices,
        total_revenue=total_revenue,
        total_payments=total_payments,
        pending_payments=pending_payments,
        low_stock_product_count=low_stock_product_count,
        today_sales=today_sales,
        today_orders=today_orders,
        current_month_revenue=current_month_revenue,
    )


def get_sales_analytics(
    db: Session,
    organization_id: UUID,
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    period_type: str = "daily",
) -> SalesAnalyticsResponse:
    """Retrieve sales and revenue analytics grouped by time interval."""
    start, end, effective_preset = parse_date_range(preset, start_date, end_date)

    orders_stmt = select(Order).where(
        Order.organization_id == organization_id,
        Order.created_at >= start,
        Order.created_at <= end,
    )
    orders = list(db.scalars(orders_stmt).all())

    payments_stmt = select(Payment).where(
        Payment.organization_id == organization_id,
        Payment.status == "COMPLETED",
        Payment.created_at >= start,
        Payment.created_at <= end,
    )
    payments = list(db.scalars(payments_stmt).all())

    invoices_stmt = select(Invoice).where(
        Invoice.organization_id == organization_id,
        Invoice.created_at >= start,
        Invoice.created_at <= end,
    )
    invoices = list(db.scalars(invoices_stmt).all())

    total_orders = len(orders)
    total_revenue = sum(
        (o.total for o in orders if o.status in ("CONFIRMED", "COMPLETED")), Decimal(0)
    )
    total_payments = sum((p.amount for p in payments), Decimal(0))
    total_invoices = sum(
        (inv.total for inv in invoices if inv.status != "VOID"), Decimal(0)
    )

    # Group by interval string format (YYYY-MM-DD for daily, YYYY-WW for weekly, YYYY-MM for monthly)
    buckets: dict[str, dict[str, Any]] = {}
    for o in orders:
        if period_type == "monthly":
            key = o.created_at.strftime("%Y-%m")
        elif period_type == "weekly":
            key = f"{o.created_at.isocalendar()[0]}-W{o.created_at.isocalendar()[1]:02d}"
        else:
            key = o.created_at.strftime("%Y-%m-%d")

        if key not in buckets:
            buckets[key] = {
                "period": key,
                "order_count": 0,
                "revenue": Decimal(0),
                "payment_total": Decimal(0),
                "invoice_total": Decimal(0),
            }
        buckets[key]["order_count"] += 1
        if o.status in ("CONFIRMED", "COMPLETED"):
            buckets[key]["revenue"] += o.total

    for p in payments:
        if period_type == "monthly":
            key = p.created_at.strftime("%Y-%m")
        elif period_type == "weekly":
            key = f"{p.created_at.isocalendar()[0]}-W{p.created_at.isocalendar()[1]:02d}"
        else:
            key = p.created_at.strftime("%Y-%m-%d")

        if key not in buckets:
            buckets[key] = {
                "period": key,
                "order_count": 0,
                "revenue": Decimal(0),
                "payment_total": Decimal(0),
                "invoice_total": Decimal(0),
            }
        buckets[key]["payment_total"] += p.amount

    for inv in invoices:
        if period_type == "monthly":
            key = inv.created_at.strftime("%Y-%m")
        elif period_type == "weekly":
            key = f"{inv.created_at.isocalendar()[0]}-W{inv.created_at.isocalendar()[1]:02d}"
        else:
            key = inv.created_at.strftime("%Y-%m-%d")

        if key not in buckets:
            buckets[key] = {
                "period": key,
                "order_count": 0,
                "revenue": Decimal(0),
                "payment_total": Decimal(0),
                "invoice_total": Decimal(0),
            }
        if inv.status != "VOID":
            buckets[key]["invoice_total"] += inv.total

    breakdown_list = [
        SalesAnalyticsItem(**data) for key, data in sorted(buckets.items())
    ]

    return SalesAnalyticsResponse(
        preset=effective_preset,
        start_date=start,
        end_date=end,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_payments=total_payments,
        total_invoices=total_invoices,
        breakdown=breakdown_list,
    )


def get_product_analytics(
    db: Session, organization_id: UUID, limit: int = 10
) -> ProductAnalyticsResponse:
    """Retrieve product performance metrics (top selling, highest revenue, low stock, inventory value)."""
    # Top selling products by quantity
    top_units_query = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            func.coalesce(func.sum(OrderItem.quantity), Decimal(0)).label("units_sold"),
            func.coalesce(func.sum(OrderItem.line_total), Decimal(0)).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Product.organization_id == organization_id,
            Order.status.in_(["CONFIRMED", "COMPLETED"]),
        )
        .group_by(Product.id, Product.sku, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )
    top_selling = [
        TopProductItem(
            product_id=row.id,
            sku=row.sku,
            name=row.name,
            units_sold=row.units_sold,
            total_revenue=row.total_revenue,
        )
        for row in db.execute(top_units_query).all()
    ]

    # Highest revenue products
    top_rev_query = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            func.coalesce(func.sum(OrderItem.quantity), Decimal(0)).label("units_sold"),
            func.coalesce(func.sum(OrderItem.line_total), Decimal(0)).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Product.organization_id == organization_id,
            Order.status.in_(["CONFIRMED", "COMPLETED"]),
        )
        .group_by(Product.id, Product.sku, Product.name)
        .order_by(func.sum(OrderItem.line_total).desc())
        .limit(limit)
    )
    highest_revenue = [
        TopProductItem(
            product_id=row.id,
            sku=row.sku,
            name=row.name,
            units_sold=row.units_sold,
            total_revenue=row.total_revenue,
        )
        for row in db.execute(top_rev_query).all()
    ]

    # Low stock products
    low_stock_query = (
        select(
            InventoryItem.id.label("inventory_item_id"),
            InventoryItem.product_id,
            InventoryItem.branch_id,
            Branch.name.label("branch_name"),
            Product.sku,
            Product.name,
            InventoryItem.quantity,
            InventoryItem.reorder_level,
        )
        .join(Branch, Branch.id == InventoryItem.branch_id)
        .join(Product, Product.id == InventoryItem.product_id)
        .where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.quantity <= InventoryItem.reorder_level,
        )
        .order_by(InventoryItem.quantity.asc())
        .limit(limit)
    )
    low_stock = [
        LowStockItem(
            inventory_item_id=row.inventory_item_id,
            product_id=row.product_id,
            branch_id=row.branch_id,
            branch_name=row.branch_name,
            sku=row.sku,
            name=row.name,
            quantity=row.quantity,
            reorder_level=row.reorder_level,
        )
        for row in db.execute(low_stock_query).all()
    ]

    # Total inventory valuation (sum of quantity * cost_price)
    inv_value_query = (
        select(
            func.coalesce(
                func.sum(InventoryItem.quantity * Product.cost_price), Decimal(0)
            )
        )
        .join(Product, Product.id == InventoryItem.product_id)
        .where(InventoryItem.organization_id == organization_id)
    )
    total_inventory_value = db.scalar(inv_value_query) or Decimal(0)

    return ProductAnalyticsResponse(
        top_selling_products=top_selling,
        highest_revenue_products=highest_revenue,
        low_stock_products=low_stock,
        total_inventory_value=total_inventory_value,
    )


def get_customer_analytics(
    db: Session,
    organization_id: UUID,
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
) -> CustomerAnalyticsResponse:
    """Retrieve customer statistics and top customer rankings."""
    start, end, _ = parse_date_range(preset, start_date, end_date)

    total_customers = (
        db.scalar(
            select(func.count(Customer.id)).where(Customer.organization_id == organization_id)
        )
        or 0
    )

    new_customers_in_period = (
        db.scalar(
            select(func.count(Customer.id)).where(
                Customer.organization_id == organization_id,
                Customer.created_at >= start,
                Customer.created_at <= end,
            )
        )
        or 0
    )

    top_customers_query = (
        select(
            Customer.id,
            Customer.name,
            Customer.email,
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total), Decimal(0)).label("total_spent"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .where(
            Customer.organization_id == organization_id,
            Order.status.in_(["CONFIRMED", "COMPLETED"]),
        )
        .group_by(Customer.id, Customer.name, Customer.email)
        .order_by(func.sum(Order.total).desc())
        .limit(limit)
    )

    top_customers = [
        TopCustomerItem(
            customer_id=row.id,
            name=row.name,
            email=row.email,
            order_count=row.order_count,
            total_spent=row.total_spent,
        )
        for row in db.execute(top_customers_query).all()
    ]

    return CustomerAnalyticsResponse(
        total_customers=total_customers,
        new_customers_in_period=new_customers_in_period,
        top_customers=top_customers,
    )


def get_branch_analytics(db: Session, organization_id: UUID) -> BranchAnalyticsResponse:
    """Retrieve performance statistics broken down per branch."""
    branches_stmt = select(Branch).where(Branch.organization_id == organization_id)
    branches = list(db.scalars(branches_stmt).all())

    branch_items: list[BranchAnalyticsItem] = []
    for b in branches:
        order_count = (
            db.scalar(
                select(func.count(Order.id)).where(
                    Order.organization_id == organization_id,
                    Order.branch_id == b.id,
                )
            )
            or 0
        )

        revenue = (
            db.scalar(
                select(func.coalesce(func.sum(Order.total), Decimal(0))).where(
                    Order.organization_id == organization_id,
                    Order.branch_id == b.id,
                    Order.status.in_(["CONFIRMED", "COMPLETED"]),
                )
            )
            or Decimal(0)
        )

        inventory_items_count = (
            db.scalar(
                select(func.count(InventoryItem.id)).where(
                    InventoryItem.organization_id == organization_id,
                    InventoryItem.branch_id == b.id,
                )
            )
            or 0
        )

        inventory_value = (
            db.scalar(
                select(
                    func.coalesce(
                        func.sum(InventoryItem.quantity * Product.cost_price), Decimal(0)
                    )
                )
                .join(Product, Product.id == InventoryItem.product_id)
                .where(
                    InventoryItem.organization_id == organization_id,
                    InventoryItem.branch_id == b.id,
                )
            )
            or Decimal(0)
        )

        branch_items.append(
            BranchAnalyticsItem(
                branch_id=b.id,
                code=b.code,
                name=b.name,
                order_count=order_count,
                revenue=revenue,
                inventory_items_count=inventory_items_count,
                inventory_value=inventory_value,
            )
        )

    return BranchAnalyticsResponse(branches=branch_items)
