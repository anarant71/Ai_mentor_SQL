"""SQLAlchemy 2.0 DeclarativeBase and TimestampMixin.

Используется всеми моделями платформы AI-Mentor.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Автоматически проставляет created_at и updated_at.

    Соответствует DEFAULT now() и триггеру set_updated_at() из platform_schema_v1.sql.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )