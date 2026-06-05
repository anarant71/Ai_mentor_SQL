"""Database engines and sessions.

Два независимых асинхронных подключения к PostgreSQL:
- platform_db — таблицы платформы (users, lessons, tasks, ...)
- training_db — учебная БД (read-only, с таймаутом)
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.config import settings


# ---------------------------------------------------------------------------
# Platform engine — read-write, ORM-сессии
# ---------------------------------------------------------------------------
platform_engine = create_async_engine(
    settings.PLATFORM_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

PlatformSessionLocal = async_sessionmaker(
    bind=platform_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_platform_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: сессия платформы (один запрос = одна сессия)."""
    async with PlatformSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Training engine — read-only, таймаут
# ---------------------------------------------------------------------------
training_engine = create_async_engine(
    settings.TRAINING_DATABASE_URL,
    pool_size=2,
    max_overflow=5,
    echo=False,
)

TrainingSessionLocal = async_sessionmaker(
    bind=training_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_training_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: сессия тренировочной БД (read-only)."""
    async with TrainingSessionLocal() as session:
        # Устанавливаем таймаут на уровне сессии
        timeout_ms = settings.TRAINING_STATEMENT_TIMEOUT * 1000
        await session.execute(
            text(f"SET statement_timeout = '{timeout_ms}'")
        )
        yield session


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------
async def check_platform_db() -> dict:
    """Проверить подключение к platform_db."""
    try:
        async with PlatformSessionLocal() as session:
            result = await session.execute(text("SELECT 1 AS ok"))
            row = result.one()
            return {"status": "ok", "detail": str(row._mapping["ok"])}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


async def check_training_db() -> dict:
    """Проверить подключение к training_db."""
    try:
        async with TrainingSessionLocal() as session:
            result = await session.execute(text("SELECT 1 AS ok"))
            row = result.one()
            return {"status": "ok", "detail": str(row._mapping["ok"])}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
async def init_databases() -> None:
    """Проверяет, что оба engine созданы (не выполняет миграции)."""
    # Просто убеждаемся, что engine может подключиться
    async with platform_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def close_databases() -> None:
    """Корректно закрывает оба engine при shutdown."""
    await platform_engine.dispose()
    await training_engine.dispose()