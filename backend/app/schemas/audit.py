from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    user_email: str | None = None
    action: str
    entity_type: str
    entity_id: UUID | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
