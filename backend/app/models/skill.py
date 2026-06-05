"""Skill, StudentSkill, TaskSkill models — таблицы skills, student_skills, task_skills."""

import uuid
from decimal import Decimal
from datetime import datetime
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .task import Task


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="basic",
    )
    icon: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="📋",
    )
    sort_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self) -> str:
        return f"Skill(id={self.id}, code={self.code}, title={self.title})"


class StudentSkill(Base, TimestampMixin):
    __tablename__ = "student_skills"

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
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_attempts: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    successful_attempts: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # relationships
    student: Mapped["User"] = relationship(back_populates="skill_progress")
    skill: Mapped["Skill"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "percentage >= 0 AND percentage <= 100",
            name="percentage_range_check",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="confidence_range_check",
        ),
        CheckConstraint(
            "total_attempts >= 0",
            name="total_attempts_check",
        ),
        CheckConstraint(
            "successful_attempts >= 0",
            name="successful_attempts_check",
        ),
        Index("idx_student_skills_student", "student_id"),
        Index("idx_student_skills_skill", "skill_id"),
        Index(
            "uq_student_skills",
            "student_id",
            "skill_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"StudentSkill(student_id={self.student_id}, "
            f"skill_id={self.skill_id}, percentage={self.percentage})"
        )


class TaskSkill(Base):
    __tablename__ = "task_skills"

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("1.00"),
    )

    # relationships
    task: Mapped["Task"] = relationship(back_populates="skill_tags")
    skill: Mapped["Skill"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "weight > 0 AND weight <= 1",
            name="weight_range_check",
        ),
        Index("idx_task_skills_task", "task_id"),
        Index("idx_task_skills_skill", "skill_id"),
    )

    def __repr__(self) -> str:
        return f"TaskSkill(task_id={self.task_id}, skill_id={self.skill_id})"