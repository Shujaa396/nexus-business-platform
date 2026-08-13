import importlib


def test_settings_loads_database_url_from_env(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@db.example.supabase.co:5432/postgres")
    import app.core.config as config_module

    importlib.reload(config_module)

    assert config_module.settings.database_url == "postgresql+psycopg://user:pass@db.example.supabase.co:5432/postgres"


def test_database_health_not_configured_when_url_missing(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import app.core.config as config_module
    import app.db.health as health_module

    importlib.reload(config_module)
    importlib.reload(health_module)

    assert health_module.database_health_status() == {
        "status": "not_configured",
        "database_url_configured": False,
    }


def test_database_ping_requires_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import app.db.session as session_module

    importlib.reload(session_module)

    assert session_module.database_ping() is False
