"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    # For simplicity, we'll use an in-memory SQLite database for testing
    engine = create_engine("sqlite:///test.db")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)