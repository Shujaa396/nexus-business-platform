from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

AnalyticsIntent = Literal[
    "sales_summary",
    "sales_trend",
    "top_products",
    "top_customers",
    "branch_performance",
    "inventory_summary",
    "payment_summary",
    "invoice_summary",
    "supplier_summary",
]
PeriodType = Literal["daily", "weekly", "monthly"]


class AnalyticsFilters(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    branch_id: UUID | None = None
    limit: int = Field(default=10, ge=1, le=50)
    period: PeriodType = "daily"

    @model_validator(mode="after")
    def validate_range(self) -> AnalyticsFilters:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be before date_to")
        if self.date_from and self.date_to and self.date_to - self.date_from > timedelta(days=366):
            raise ValueError("Analytics date range cannot exceed 366 days")
        return self


class AnalyticsQueryRequest(AnalyticsFilters):
    intent: AnalyticsIntent


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    filters: AnalyticsFilters = Field(default_factory=AnalyticsFilters)


class AnalyticsResponse(BaseModel):
    intent: AnalyticsIntent
    date_from: datetime
    date_to: datetime
    data: dict[str, Any]


class NaturalLanguageQueryResponse(BaseModel):
    supported: bool
    message: str
    intent: AnalyticsIntent | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    data: dict[str, Any] | None = None


def normalized_range(filters: AnalyticsFilters) -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    end = filters.date_to or now
    start = filters.date_from or (end - timedelta(days=30))
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    return start, end
