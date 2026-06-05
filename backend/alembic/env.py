"""Alembic environment configuration.

Загружает модели через Base.metadata для autogenerate.
Использует sync-драйвер (psycopg2) для выполнения миграций.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Импорт моделей — регистрирует их в Base.metadata для autogenerate
from app.models import Base
from app.config import settings

# Alembic Config object
config = context.config

# Настройка логов из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata для autogenerate
target_metadata = Base.metadata

# Подставляем sync URL из настроек приложения
sync_url = settings.PLATFORM_DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql://"
)
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (SQL скрипт, без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций через sync-движок psycopg2."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()