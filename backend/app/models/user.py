"""User и StudentProfile — пользователи платформы и их профили.

Соответствует таблицам users и student_profiles из platform_schema_v1.sql.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .submission import Submission
    from .progress import LessonProgress
    from .mistake import StudentMistake
    from .roadmap import Roadmap, Recommendation


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )

    # tail columns from TimestampMixin: created_at, updated_at

    # relationships
    profile: Mapped["StudentProfile"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    lesson_progress_entries: Mapped[list["LessonProgress"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    skill_progress: Mapped[list["StudentSkill"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    mistakes: Mapped[list["StudentMistake"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    roadmaps: Mapped[list["Roadmap"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="role_check"),
        CheckConstraint(
            "status IN ('active', 'blocked')",
            name="users_status_check",
        ),
        Index("idx_users_status", "status"),
        Index("idx_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, role={self.role})"


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    learning_goal: Mapped[Optional[str]] = mapped_column(nullable=True)
    current_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="beginner",
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ru",
    )
    weekly_study_minutes: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Asia/Almaty",
    )

    # tail columns from TimestampMixin: created_at, updated_at

    # relationships
    user: Mapped["User"] = relationship(back_populates="profile")

    __table_args__ = (
        CheckConstraint(
            "current_level IN ('beginner', 'intermediate', 'advanced')",
            name="current_level_check",
        ),
        CheckConstraint(
            "weekly_study_minutes >= 0",
            name="weekly_study_minutes_check",
        ),
        CheckConstraint(
            "char_length(timezone) > 0",
            name="timezone_not_empty_check",
        ),
        Index("idx_student_profiles_current_level", "current_level"),
    )

    def __repr__(self) -> str:
        return f"StudentProfile(user_id={self.user_id}, level={self.current_level})"