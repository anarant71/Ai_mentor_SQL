"""Pytest configuration — clean data between tests via PostgreSQL.

Uses synchronous SQLAlchemy for test fixtures (event-loop-agnostic),
while tests themselves use async httpx.AsyncClient + starlette's own loop.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.base import Base

_sync_url = settings.PLATFORM_DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql://"
).replace(
    "postgresql+psycopg2://", "postgresql://"
)

_sync_engine = create_engine(_sync_url)


@pytest.fixture(scope="session", autouse=True)
def _ensure_tables():
    """Create all tables (idempotent) before test session."""
    Base.metadata.create_all(bind=_sync_engine)
    yield
    Base.metadata.drop_all(bind=_sync_engine)


@pytest.fixture(autouse=True)
def _clear_db():
    """Delete all data from all tables between tests."""
    with _sync_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture
def client():
    """Return TestClient that manages its own async loop."""
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as tc:
        yield tc
