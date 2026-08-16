from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def log_activity(
    db: Session,
    *,
    organization_id: UUID,
    user: User | None = None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        organization_id=organization_id,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        action=action.upper(),
        entity_type=entity_type.upper(),
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.flush()
    return entry
