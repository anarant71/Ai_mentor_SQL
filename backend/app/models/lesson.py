"""Lesson model — таблица lessons.

Соответствует таблице lessons из platform_schema_v1.sql.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .task import Task
    from .progress import LessonProgress


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    module_number: Mapped[int] = mapped_column(nullable=False)
    lesson_number: Mapped[int] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(nullable=False)
    module_title: Mapped[str] = mapped_column(nullable=False)
    summary: Mapped[str] = mapped_column(nullable=False)
    content_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )
    difficulty: Mapped[int] = mapped_column(nullable=False, default=1)
    estimated_minutes: Mapped[int] = mapped_column(nullable=False, default=15)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="published",
    )

    # tail columns from TimestampMixin: created_at, updated_at

    # relationships
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    progress_entries: Mapped[list["LessonProgress"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("module_number", "lesson_number", name="module_lesson_unique"),
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="lessons_difficulty_check"),
        CheckConstraint("estimated_minutes > 0", name="estimated_minutes_check"),
        CheckConstraint(
            "status IN ('published', 'draft', 'archived')",
            name="lessons_status_check",
        ),
        CheckConstraint(
            "module_number BETWEEN 0 AND 10",
            name="module_number_check",
        ),
        CheckConstraint(
            "lesson_number BETWEEN 1 AND 50",
            name="lesson_number_check",
        ),
        Index("idx_lessons_status", "status"),
        Index("idx_lessons_module_lesson", "module_number", "lesson_number"),
        Index("idx_lessons_difficulty", "difficulty"),
    )

    def __repr__(self) -> str:
        return f"Lesson(id={self.id}, slug={self.slug}, title={self.title})"