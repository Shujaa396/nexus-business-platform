from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.db.session import database_ping


def database_health_status() -> dict[str, Any]:
    if not settings.database_url:
        return {"status": "not_configured", "database_url_configured": False}

    if database_ping():
        return {"status": "ok", "database_url_configured": True}

    return {"status": "unavailable", "database_url_configured": True}
