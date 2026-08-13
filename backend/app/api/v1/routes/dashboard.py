from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_membership
from app.db.session import get_db
from app.schemas.dashboard import (
    BranchAnalyticsResponse,
    CustomerAnalyticsResponse,
    DashboardSummaryResponse,
    ProductAnalyticsResponse,
    SalesAnalyticsResponse,
)
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve overall business metrics for the authenticated organization's dashboard."""
    org_id = membership.organization_id
    return dashboard_service.get_dashboard_summary(db, org_id)


@router.get("/sales", response_model=SalesAnalyticsResponse)
def get_sales_analytics(
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    period_type: str = "daily",
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve sales, order volume, payment, and invoice totals grouped by interval."""
    org_id = membership.organization_id
    return dashboard_service.get_sales_analytics(
        db,
        organization_id=org_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        period_type=period_type,
    )


@router.get("/sales/daily", response_model=SalesAnalyticsResponse)
def get_daily_sales_analytics(
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Shortcut endpoint for daily sales analytics."""
    org_id = membership.organization_id
    return dashboard_service.get_sales_analytics(
        db,
        organization_id=org_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        period_type="daily",
    )


@router.get("/sales/weekly", response_model=SalesAnalyticsResponse)
def get_weekly_sales_analytics(
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Shortcut endpoint for weekly sales analytics."""
    org_id = membership.organization_id
    return dashboard_service.get_sales_analytics(
        db,
        organization_id=org_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        period_type="weekly",
    )


@router.get("/sales/monthly", response_model=SalesAnalyticsResponse)
def get_monthly_sales_analytics(
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Shortcut endpoint for monthly sales analytics."""
    org_id = membership.organization_id
    return dashboard_service.get_sales_analytics(
        db,
        organization_id=org_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        period_type="monthly",
    )


@router.get("/products", response_model=ProductAnalyticsResponse)
def get_product_analytics(
    limit: int = 10,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve top selling, highest revenue, low stock products, and inventory valuation."""
    org_id = membership.organization_id
    return dashboard_service.get_product_analytics(db, org_id, limit=limit)


@router.get("/customers", response_model=CustomerAnalyticsResponse)
def get_customer_analytics(
    preset: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve customer totals, new customer signups, and top spenders."""
    org_id = membership.organization_id
    return dashboard_service.get_customer_analytics(
        db,
        organization_id=org_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/branches", response_model=BranchAnalyticsResponse)
def get_branch_analytics(
    membership=Depends(get_current_membership),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve branch-wise sales, order volume, and inventory value statistics."""
    org_id = membership.organization_id
    return dashboard_service.get_branch_analytics(db, org_id)
