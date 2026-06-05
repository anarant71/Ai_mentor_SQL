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


class Roadmap(Base, TimestampMixin):
    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="automatic"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    student: Mapped["User"] = relationship(back_populates="roadmaps")
    steps: Mapped[list["RoadmapStep"]] = relationship(
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapStep.position",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'paused', 'archived')",
            name="roadmaps_status_check",
        ),
        CheckConstraint(
            "source IN ('diagnostic', 'manual', 'automatic')",
            name="roadmaps_source_check",
        ),
        Index("idx_roadmaps_student_status", "student_id", "status"),
    )

    def __repr__(self) -> str:
        return f"Roadmap(id={self.id}, student={self.student_id}, status={self.status})"


class RoadmapStep(Base, TimestampMixin):
    __tablename__ = "roadmap_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="locked"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    roadmap: Mapped["Roadmap"] = relationship(back_populates="steps")

    __table_args__ = (
        CheckConstraint(
            "position > 0",
            name="roadmap_steps_position_check",
        ),
        CheckConstraint(
            "step_type IN ('lesson', 'task', 'practice', 'review', 'assessment', 'project')",
            name="roadmap_steps_type_check",
        ),
        CheckConstraint(
            "status IN ('locked', 'available', 'in_progress', 'completed', 'skipped')",
            name="roadmap_steps_status_check",
        ),
        Index("idx_roadmap_steps_roadmap_position", "roadmap_id", "position"),
        Index("idx_roadmap_steps_status", "status"),
    )

    def __repr__(self) -> str:
        return f"RoadmapStep(id={self.id}, pos={self.position}, status={self.status})"


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    rec_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    student: Mapped["User"] = relationship(back_populates="recommendations")

    __table_args__ = (
        CheckConstraint(
            "rec_type IN ('next_lesson', 'practice', 'review', 'project', 'assessment')",
            name="recommendations_type_check",
        ),
        CheckConstraint(
            "priority >= 0",
            name="recommendations_priority_check",
        ),
        CheckConstraint(
            "status IN ('new', 'shown', 'accepted', 'dismissed', 'completed')",
            name="recommendations_status_check",
        ),
        Index("idx_recommendations_student_status", "student_id", "status"),
        Index("idx_recommendations_priority", "priority"),
    )

    def __repr__(self) -> str:
        return f"Recommendation(id={self.id}, type={self.rec_type}, status={self.status})"