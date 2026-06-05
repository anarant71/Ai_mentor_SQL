"""Submission model — таблица submissions.

Соответствует таблице submissions из platform_schema_v1.sql.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .task import Task


class Submission(Base):
    __tablename__ = "submissions"

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
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tasks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(nullable=False)
    sql_text: Mapped[str] = mapped_column(nullable=False)
    execution_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="submitted",
    )
    execution_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 3),
        nullable=True,
    )
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # relationships
    student: Mapped["User"] = relationship(back_populates="submissions")
    task: Mapped["Task"] = relationship(back_populates="submissions")

    __table_args__ = (
        CheckConstraint(
            "attempt_number > 0",
            name="attempt_number_positive_check",
        ),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 1)",
            name="score_range_check",
        ),
        CheckConstraint(
            "execution_status IN ('submitted', 'syntax_error', 'executed', 'reviewed', 'accepted', 'rejected')",
            name="execution_status_check",
        ),
        CheckConstraint(
            "char_length(sql_text) > 0",
            name="sql_text_not_empty_check",
        ),
        Index("idx_submissions_student_id", "student_id"),
        Index("idx_submissions_task_id", "task_id"),
        Index("idx_submissions_student_task", "student_id", "task_id"),
        Index("idx_submissions_execution_status", "execution_status"),
        Index(
            "idx_submissions_is_correct",
            "is_correct",
            postgresql_where=text("is_correct IS NOT NULL"),
        ),
        Index("idx_submissions_submitted_at", "submitted_at", postgresql_ops={"submitted_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return (
            f"Submission(id={self.id}, student_id={self.student_id}, "
            f"task_id={self.task_id}, attempt={self.attempt_number})"
        )