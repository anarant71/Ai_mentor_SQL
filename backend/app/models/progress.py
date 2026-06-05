"""LessonProgress model — таблица lesson_progress.

Соответствует таблице lesson_progress из platform_schema_v1.sql.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .lesson import Lesson


class LessonProgress(Base, TimestampMixin):
    __tablename__ = "lesson_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_started",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # tail columns from TimestampMixin: created_at, updated_at

    # relationships
    student: Mapped["User"] = relationship(
        back_populates="lesson_progress_entries"
    )
    lesson: Mapped["Lesson"] = relationship(
        back_populates="progress_entries"
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "lesson_id", name="student_lesson_unique"
        ),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed', 'skipped')",
            name="lesson_progress_status_check",
        ),
        CheckConstraint(
            "completed_at IS NULL OR started_at IS NOT NULL",
            name="dates_consistency_check",
        ),
        CheckConstraint(
            "completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at",
            name="completed_not_before_started_check",
        ),
        Index("idx_lesson_progress_student_id", "student_id"),
        Index("idx_lesson_progress_lesson_id", "lesson_id"),
        Index("idx_lesson_progress_student_status", "student_id", "status"),
        Index("idx_lesson_progress_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"LessonProgress(id={self.id}, student_id={self.student_id}, "
            f"lesson_id={self.lesson_id}, status={self.status})"
        )