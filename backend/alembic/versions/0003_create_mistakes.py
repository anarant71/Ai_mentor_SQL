"""Create mistake_types and student_mistakes tables.

Revision ID: 0003
Revises: 0002
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mistake_types",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("domain", sa.String(50), nullable=False, server_default="sql"),
        sa.Column("severity_default", sa.Integer, nullable=False, server_default="2"),
        sa.CheckConstraint(
            "severity_default BETWEEN 1 AND 5",
            name="mistake_types_severity_check",
        ),
    )

    op.create_index("idx_mistake_types_code", "mistake_types", ["code"])
    op.create_index("idx_mistake_types_domain", "mistake_types", ["domain"])

    op.create_table(
        "student_mistakes",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mistake_type_id", UUID, sa.ForeignKey("mistake_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", UUID, sa.ForeignKey("skills.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submission_id", UUID, sa.ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("severity", sa.Integer, nullable=False, server_default="2"),
        sa.Column("repeat_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "severity BETWEEN 1 AND 5",
            name="student_mistakes_severity_check",
        ),
        sa.CheckConstraint(
            "repeat_count >= 0",
            name="student_mistakes_repeat_count_check",
        ),
        sa.CheckConstraint(
            "status IN ('new', 'active', 'training', 'resolved', 'ignored')",
            name="student_mistakes_status_check",
        ),
    )

    op.create_index(
        "idx_student_mistakes_student_status",
        "student_mistakes",
        ["student_id", "status"],
    )
    op.create_index(
        "idx_student_mistakes_skill",
        "student_mistakes",
        ["skill_id"],
    )
    op.create_index(
        "idx_student_mistakes_type",
        "student_mistakes",
        ["mistake_type_id"],
    )
    op.create_index(
        "idx_student_mistakes_last_seen",
        "student_mistakes",
        ["last_seen_at"],
    )


def downgrade() -> None:
    op.drop_table("student_mistakes")
    op.drop_table("mistake_types")