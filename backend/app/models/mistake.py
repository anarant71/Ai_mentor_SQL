import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .submission import Submission


class MistakeType(Base):
    __tablename__ = "mistake_types"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(
        String(50), nullable=False, default="sql"
    )
    severity_default: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2
    )

    __table_args__ = (
        CheckConstraint(
            "severity_default BETWEEN 1 AND 5",
            name="mistake_types_severity_check",
        ),
        Index("idx_mistake_types_code", "code"),
        Index("idx_mistake_types_domain", "domain"),
    )

    def __repr__(self) -> str:
        return f"MistakeType(id={self.id}, code={self.code})"


class StudentMistake(Base, TimestampMixin):
    __tablename__ = "student_mistakes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    mistake_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("mistake_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
    )
    submission_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("submissions.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    repeat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new"
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    student: Mapped["User"] = relationship(back_populates="mistakes")
    mistake_type: Mapped["MistakeType"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "severity BETWEEN 1 AND 5",
            name="student_mistakes_severity_check",
        ),
        CheckConstraint(
            "repeat_count >= 0",
            name="student_mistakes_repeat_count_check",
        ),
        CheckConstraint(
            "status IN ('new', 'active', 'training', 'resolved', 'ignored')",
            name="student_mistakes_status_check",
        ),
        Index("idx_student_mistakes_student_status", "student_id", "status"),
        Index("idx_student_mistakes_skill", "skill_id"),
        Index("idx_student_mistakes_type", "mistake_type_id"),
        Index("idx_student_mistakes_last_seen", "last_seen_at"),
    )

    def __repr__(self) -> str:
        return (
            f"StudentMistake(id={self.id}, student_id={self.student_id}, "
            f"code={self.mistake_type.code if self.mistake_type else '?'}, "
            f"status={self.status})"
        )