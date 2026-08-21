from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

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
    PurchaseOrder,
    Supplier,
)
from app.schemas.analytics import AnalyticsFilters, AnalyticsIntent, normalized_range

SALES_STATUSES = ("CONFIRMED", "COMPLETED")


def _money(value: Decimal | int | None) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(value or 0)


def _filters(query: Any, organization_id: UUID, filters: AnalyticsFilters, start: datetime, end: datetime) -> Any:
    query = query.filter(
        Order.organization_id == organization_id,
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status.in_(SALES_STATUSES),
    )
    if filters.branch_id:
        query = query.filter(Order.branch_id == filters.branch_id)
    return query


def sales_summary(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    query = db.query(Order).filter(
        Order.organization_id == organization_id,
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status.in_(SALES_STATUSES),
    )
    if filters.branch_id:
        query = query.filter(Order.branch_id == filters.branch_id)
    orders = query.all()
    total_sales = sum((_money(order.total) for order in orders), Decimal(0))
    return {
        "total_sales": total_sales,
        "order_count": len(orders),
        "average_order_value": total_sales / len(orders) if orders else Decimal(0),
    }


def _bucket(value: datetime, period: str) -> str:
    if period == "monthly":
        return value.strftime("%Y-%m")
    if period == "weekly":
        iso = value.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return value.strftime("%Y-%m-%d")


def sales_trend(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    query = db.query(Order).filter(
        Order.organization_id == organization_id,
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status.in_(SALES_STATUSES),
    )
    if filters.branch_id:
        query = query.filter(Order.branch_id == filters.branch_id)
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"period": "", "sales": Decimal(0), "order_count": 0})
    for order in query.all():
        key = _bucket(order.created_at, filters.period)
        buckets[key]["period"] = key
        buckets[key]["sales"] += _money(order.total)
        buckets[key]["order_count"] += 1
    return {"breakdown": [buckets[key] for key in sorted(buckets)]}


def top_products(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    query = (
        db.query(OrderItem, Product, Order)
        .join(Product, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Product.organization_id == organization_id,
            Order.organization_id == organization_id,
            Order.created_at >= start,
            Order.created_at <= end,
            Order.status.in_(SALES_STATUSES),
        )
    )
    if filters.branch_id:
        query = query.filter(Order.branch_id == filters.branch_id)
    grouped: dict[UUID, dict[str, Any]] = {}
    for item, product, _ in query.all():
        row = grouped.setdefault(product.id, {"product_id": product.id, "sku": product.sku, "name": product.name, "quantity": Decimal(0), "revenue": Decimal(0)})
        row["quantity"] += _money(item.quantity)
        row["revenue"] += _money(item.line_total)
    return {"products": sorted(grouped.values(), key=lambda row: row["revenue"], reverse=True)[: filters.limit]}


def top_customers(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    query = db.query(Order, Customer).join(Customer, Customer.id == Order.customer_id).filter(
        Order.organization_id == organization_id,
        Customer.organization_id == organization_id,
        Order.customer_id.is_not(None),
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status.in_(SALES_STATUSES),
    )
    if filters.branch_id:
        query = query.filter(Order.branch_id == filters.branch_id)
    grouped: dict[UUID, dict[str, Any]] = {}
    for order, customer in query.all():
        row = grouped.setdefault(customer.id, {"customer_id": customer.id, "name": customer.name, "email": customer.email, "order_count": 0, "revenue": Decimal(0)})
        row["order_count"] += 1
        row["revenue"] += _money(order.total)
    return {"customers": sorted(grouped.values(), key=lambda row: row["revenue"], reverse=True)[: filters.limit]}


def branch_performance(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    branches = db.query(Branch).filter(Branch.organization_id == organization_id).all()
    result = []
    for branch in branches:
        query = db.query(Order).filter(
            Order.organization_id == organization_id,
            Order.branch_id == branch.id,
            Order.created_at >= start,
            Order.created_at <= end,
            Order.status.in_(SALES_STATUSES),
        )
        orders = query.all()
        result.append({"branch_id": branch.id, "code": branch.code, "name": branch.name, "order_count": len(orders), "sales": sum((_money(order.total) for order in orders), Decimal(0))})
    return {"branches": sorted(result, key=lambda row: row["sales"], reverse=True)}


def inventory_summary(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    query = db.query(InventoryItem, Product, Branch).join(Product, Product.id == InventoryItem.product_id).join(Branch, Branch.id == InventoryItem.branch_id).filter(InventoryItem.organization_id == organization_id)
    if filters.branch_id:
        query = query.filter(InventoryItem.branch_id == filters.branch_id)
    low_stock = []
    out_of_stock = []
    inventory_value = Decimal(0)
    for item, product, branch in query.all():
        inventory_value += _money(item.quantity) * _money(product.cost_price)
        row = {"product_id": product.id, "sku": product.sku, "name": product.name, "branch_id": branch.id, "branch_name": branch.name, "quantity": item.quantity, "reorder_level": item.reorder_level}
        if item.quantity <= item.reorder_level:
            low_stock.append(row)
        if item.quantity <= 0:
            out_of_stock.append(row)
    return {"low_stock": low_stock[: filters.limit], "out_of_stock": out_of_stock[: filters.limit], "inventory_value": inventory_value}


def payment_summary(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    query = db.query(Payment).filter(Payment.organization_id == organization_id, Payment.created_at >= start, Payment.created_at <= end)
    if filters.branch_id:
        query = query.join(Order, Order.id == Payment.order_id).filter(Order.branch_id == filters.branch_id)
    by_method: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    by_status: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    total = Decimal(0)
    for payment in query.all():
        amount = _money(payment.amount)
        total += amount
        by_method[payment.payment_method] += amount
        by_status[payment.status] += amount
    return {"total": total, "by_method": [{"method": key, "total": value} for key, value in sorted(by_method.items())], "by_status": [{"status": key, "total": value} for key, value in sorted(by_status.items())]}


def invoice_summary(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    query = db.query(Invoice).filter(Invoice.organization_id == organization_id, Invoice.created_at >= start, Invoice.created_at <= end)
    if filters.branch_id:
        query = query.filter(Invoice.branch_id == filters.branch_id)
    invoices = query.all()
    now = datetime.now(UTC)
    status_counts: dict[str, int] = defaultdict(int)
    overdue_count = 0
    total = Decimal(0)
    for invoice in invoices:
        status_counts[invoice.status] += 1
        due_date = invoice.due_date
        if due_date and due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=UTC)
        if invoice.status not in ("PAID", "VOID") and due_date and due_date < now:
            overdue_count += 1
        if invoice.status != "VOID":
            total += _money(invoice.total)
    return {"total": total, "invoice_count": len(invoices), "status_counts": dict(status_counts), "overdue_count": overdue_count}


def supplier_summary(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    products = db.query(Product, Supplier).join(Supplier, Supplier.id == Product.supplier_id).filter(Product.organization_id == organization_id, Supplier.organization_id == organization_id).all()
    grouped: dict[UUID, dict[str, Any]] = {}
    for product, supplier in products:
        row = grouped.setdefault(supplier.id, {"supplier_id": supplier.id, "supplier_name": supplier.name, "product_count": 0, "inventory_value": Decimal(0)})
        row["product_count"] += 1
        inventory_items = db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id, InventoryItem.product_id == product.id)
        if filters.branch_id:
            inventory_items = inventory_items.filter(InventoryItem.branch_id == filters.branch_id)
        row["inventory_value"] += sum((_money(item.quantity) * _money(product.cost_price) for item in inventory_items.all()), Decimal(0))
    return {"suppliers": sorted(grouped.values(), key=lambda row: row["product_count"], reverse=True)[: filters.limit]}


def procurement_summary(db: Session, organization_id: UUID, filters: AnalyticsFilters) -> dict[str, Any]:
    start, end = normalized_range(filters)
    query = db.query(PurchaseOrder, Supplier).join(Supplier, Supplier.id == PurchaseOrder.supplier_id).filter(
        PurchaseOrder.organization_id == organization_id,
        Supplier.organization_id == organization_id,
        PurchaseOrder.order_date >= start,
        PurchaseOrder.order_date <= end,
    )
    if filters.branch_id:
        query = query.filter(PurchaseOrder.branch_id == filters.branch_id)
    orders = query.all()
    status_counts: dict[str, int] = defaultdict(int)
    supplier_totals: dict[UUID, dict[str, Any]] = {}
    purchasing_total = Decimal(0)
    for order, supplier in orders:
        status_counts[order.status] += 1
        if order.status != "CANCELLED":
            purchasing_total += _money(order.total)
        row = supplier_totals.setdefault(supplier.id, {"supplier_id": supplier.id, "supplier_name": supplier.name, "purchase_order_count": 0, "purchasing_total": Decimal(0)})
        row["purchase_order_count"] += 1
        if order.status != "CANCELLED":
            row["purchasing_total"] += _money(order.total)
    return {
        "purchase_order_count": len(orders),
        "pending_approvals": status_counts.get("SUBMITTED", 0),
        "pending_receipts": status_counts.get("APPROVED", 0) + status_counts.get("PARTIALLY_RECEIVED", 0),
        "purchasing_total": purchasing_total,
        "status_counts": dict(status_counts),
        "top_suppliers": sorted(supplier_totals.values(), key=lambda row: row["purchasing_total"], reverse=True)[: filters.limit],
    }


def execute(db: Session, organization_id: UUID, intent: AnalyticsIntent, filters: AnalyticsFilters) -> tuple[datetime, datetime, dict[str, Any]]:
    operations = {
        "sales_summary": sales_summary,
        "sales_trend": sales_trend,
        "top_products": top_products,
        "top_customers": top_customers,
        "branch_performance": branch_performance,
        "inventory_summary": inventory_summary,
        "payment_summary": payment_summary,
        "invoice_summary": invoice_summary,
        "supplier_summary": supplier_summary,
        "procurement_summary": procurement_summary,
    }
    start, end = normalized_range(filters)
    return start, end, operations[intent](db, organization_id, filters)


def parse_question(question: str) -> AnalyticsIntent | None:
    normalized = question.strip().lower()
    if any(term in normalized for term in ("top product", "best selling product", "best-selling product")):
        return "top_products"
    if any(term in normalized for term in ("top customer", "best customer", "highest spending customer")):
        return "top_customers"
    if "branch" in normalized and any(term in normalized for term in ("sales", "revenue", "performance")):
        return "branch_performance"
    if any(term in normalized for term in ("low stock", "out of stock", "inventory")):
        return "inventory_summary"
    if "payment" in normalized:
        return "payment_summary"
    if "invoice" in normalized:
        return "invoice_summary"
    if "supplier" in normalized or "vendor" in normalized:
        return "supplier_summary"
    if any(term in normalized for term in ("sales trend", "sales over time", "daily sales", "weekly sales", "monthly sales")):
        return "sales_trend"
    if any(term in normalized for term in ("sales", "revenue", "sold", "sell")):
        return "sales_summary"
    return None


def filters_for_question(question: str, filters: AnalyticsFilters) -> AnalyticsFilters:
    normalized = question.strip().lower()
    now = datetime.now(UTC)
    date_from = filters.date_from
    date_to = filters.date_to

    if "today" in normalized:
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = now
    elif "this month" in normalized:
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = now
    elif "last month" in normalized:
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = current_month - timedelta(microseconds=1)
        date_from = date_to.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        match = re.search(r"last\s+(\d{1,3})\s+days?", normalized)
        if match:
            days = min(int(match.group(1)), 366)
            date_from = now - timedelta(days=days)
            date_to = now

    period = filters.period
    if "weekly" in normalized:
        period = "weekly"
    elif "monthly" in normalized:
        period = "monthly"
    return filters.model_copy(update={"date_from": date_from, "date_to": date_to, "period": period})
