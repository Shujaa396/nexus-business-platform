from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsFilters,
    AnalyticsQueryRequest,
    AnalyticsResponse,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
)
from app.services import analytics as analytics_service
from app.services.audit import log_activity

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _execute(
    payload: AnalyticsQueryRequest,
    membership: Any,
    db: Session,
) -> AnalyticsResponse:
    try:
        start, end, data = analytics_service.execute(
            db,
            membership.organization_id,
            payload.intent,
            payload,
        )
        log_activity(
            db,
            organization_id=membership.organization_id,
            user=membership.user,
            action="ANALYTICS_QUERY_EXECUTED",
            entity_type="ANALYTICS",
            details=f"Executed controlled analytics intent: {payload.intent}",
        )
        db.commit()
        return AnalyticsResponse(intent=payload.intent, date_from=start, date_to=end, data=data)
    except Exception as exc:
        db.rollback()
        if isinstance(exc, ValueError | KeyError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analytics request could not be completed") from exc


def _filters(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    branch_id: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
) -> AnalyticsFilters:
    try:
        return AnalyticsFilters(date_from=date_from, date_to=date_to, branch_id=branch_id, limit=limit, period=period)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(exc.errors()),
        ) from exc


@router.get("/sales-summary", response_model=AnalyticsResponse)
def sales_summary(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="sales_summary", **filters.model_dump()), membership, db)


@router.get("/sales-trend", response_model=AnalyticsResponse)
def sales_trend(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="sales_trend", **filters.model_dump()), membership, db)


@router.get("/top-products", response_model=AnalyticsResponse)
def top_products(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="top_products", **filters.model_dump()), membership, db)


@router.get("/top-customers", response_model=AnalyticsResponse)
def top_customers(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="top_customers", **filters.model_dump()), membership, db)


@router.get("/branches", response_model=AnalyticsResponse)
def branches(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="branch_performance", **filters.model_dump()), membership, db)


@router.get("/inventory", response_model=AnalyticsResponse)
def inventory(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="inventory_summary", **filters.model_dump()), membership, db)


@router.get("/payments", response_model=AnalyticsResponse)
def payments(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="payment_summary", **filters.model_dump()), membership, db)


@router.get("/invoices", response_model=AnalyticsResponse)
def invoices(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="invoice_summary", **filters.model_dump()), membership, db)


@router.get("/suppliers", response_model=AnalyticsResponse)
def suppliers(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="supplier_summary", **filters.model_dump()), membership, db)


@router.get("/procurement", response_model=AnalyticsResponse)
def procurement(
    filters: AnalyticsFilters = Depends(_filters),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    return _execute(AnalyticsQueryRequest(intent="procurement_summary", **filters.model_dump()), membership, db)


@router.post("/query", response_model=NaturalLanguageQueryResponse)
def natural_language_query(
    payload: NaturalLanguageQueryRequest,
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    intent = analytics_service.parse_question(payload.question)
    if intent is None:
        log_activity(
            db,
            organization_id=membership.organization_id,
            user=membership.user,
            action="ANALYTICS_QUERY_UNSUPPORTED",
            entity_type="ANALYTICS",
            details="Received unsupported natural-language analytics question",
        )
        db.commit()
        return NaturalLanguageQueryResponse(
            supported=False,
            message="That question is outside the supported business analytics capabilities.",
        )

    try:
        filters = analytics_service.filters_for_question(payload.question, payload.filters)
        start, end, data = analytics_service.execute(
            db,
            membership.organization_id,
            intent,
            filters,
        )
        log_activity(
            db,
            organization_id=membership.organization_id,
            user=membership.user,
            action="ANALYTICS_NL_QUERY_EXECUTED",
            entity_type="ANALYTICS",
            details=f"Executed controlled natural-language intent: {intent}",
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analytics request could not be completed") from exc

    return NaturalLanguageQueryResponse(
        supported=True,
        message=f"Answered using the supported {intent.replace('_', ' ')} capability.",
        intent=intent,
        date_from=start,
        date_to=end,
        data=data,
    )
