"""Task model — таблица tasks."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .lesson import Lesson
    from .submission import Submission
    from .skill import TaskSkill


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=True,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    instructions: Mapped[str] = mapped_column(nullable=False)
    expected_result_text: Mapped[Optional[str]] = mapped_column(nullable=True)
    hint: Mapped[Optional[str]] = mapped_column(nullable=True)
    expected_answer_sql: Mapped[str] = mapped_column(nullable=False)
    validation_strategy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="exact_match",
    )
    difficulty: Mapped[int] = mapped_column(nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="published",
    )

    # relationships
    lesson: Mapped[Optional["Lesson"]] = relationship(back_populates="tasks")
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
    skill_tags: Mapped[list["TaskSkill"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "validation_strategy IN ('exact_match', 'sql_result', 'not_empty', 'ai', 'manual')",
            name="validation_strategy_check",
        ),
        CheckConstraint(
            "difficulty BETWEEN 1 AND 5",
            name="tasks_difficulty_check",
        ),
        CheckConstraint(
            "status IN ('published', 'draft', 'archived')",
            name="tasks_status_check",
        ),
        Index("idx_tasks_lesson_id", "lesson_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_difficulty", "difficulty"),
    )

    def __repr__(self) -> str:
        return f"Task(id={self.id}, slug={self.slug}, title={self.title})"