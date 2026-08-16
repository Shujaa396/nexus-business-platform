from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    user_id: UUID | None = Query(None),
    membership=Depends(require_role(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    q = db.query(AuditLog).filter(AuditLog.organization_id == org_id)

    if action:
        q = q.filter(AuditLog.action == action.upper())
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type.upper())
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)

    q = q.order_by(AuditLog.created_at.desc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items
