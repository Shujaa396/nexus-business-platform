import os
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_engine() -> Engine:
    settings = get_settings()
    if not settings.database_url:
        # During pytest runs, allow a local sqlite file to be used for tests
        if os.getenv("PYTEST_CURRENT_TEST"):
            return create_engine("sqlite:///./test.db", pool_pre_ping=True, future=True)
        raise RuntimeError("DATABASE_URL is not configured.")

    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


def get_session_factory() -> sessionmaker[Session]:
    engine = get_engine()
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )


def get_db() -> Generator[Session, None, None]:
    settings = get_settings()
    if not settings.database_url:
        # allow pytest-local sqlite fallback
        if not os.getenv("PYTEST_CURRENT_TEST"):
            raise RuntimeError("DATABASE_URL is not configured.")

    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def database_ping() -> bool:
    settings = get_settings()
    if not settings.database_url:
        return False

    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
