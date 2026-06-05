"""Create all 6 platform tables.

Создаёт таблицы: users, student_profiles, lessons, tasks, submissions, lesson_progress.
Соответствует platform_schema_v1.sql и SQLAlchemy моделям.

Revision ID: 0001
Revises:
Create Date: 2026-05-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. users
    # -----------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column(
            "role", sa.String(20), nullable=False, server_default="student"
        ),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="active"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint("email_unique", "users", ["email"])
    op.create_check_constraint(
        "role_check", "users", "role IN ('student', 'admin')"
    )
    op.create_check_constraint(
        "users_status_check", "users", "status IN ('active', 'blocked')"
    )
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index("idx_users_role", "users", ["role"])

    # -----------------------------------------------------------------------
    # 2. lessons
    # -----------------------------------------------------------------------
    op.create_table(
        "lessons",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("module_number", sa.Integer, nullable=False),
        sa.Column("lesson_number", sa.Integer, nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("module_title", sa.String, nullable=False),
        sa.Column("summary", sa.String, nullable=False),
        sa.Column("content_path", sa.String(500), nullable=False),
        sa.Column(
            "difficulty", sa.Integer, nullable=False, server_default="1"
        ),
        sa.Column(
            "estimated_minutes",
            sa.Integer,
            nullable=False,
            server_default="15",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="published",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint("slug_unique", "lessons", ["slug"])
    op.create_unique_constraint(
        "module_lesson_unique", "lessons", ["module_number", "lesson_number"]
    )
    op.create_unique_constraint(
        "content_path_unique", "lessons", ["content_path"]
    )
    op.create_check_constraint(
        "lessons_difficulty_check",
        "lessons",
        "difficulty BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "estimated_minutes_check", "lessons", "estimated_minutes > 0"
    )
    op.create_check_constraint(
        "lessons_status_check",
        "lessons",
        "status IN ('published', 'draft', 'archived')",
    )
    op.create_check_constraint(
        "module_number_check",
        "lessons",
        "module_number BETWEEN 0 AND 10",
    )
    op.create_check_constraint(
        "lesson_number_check",
        "lessons",
        "lesson_number BETWEEN 1 AND 50",
    )
    op.create_index("idx_lessons_status", "lessons", ["status"])
    op.create_index(
        "idx_lessons_module_lesson",
        "lessons",
        ["module_number", "lesson_number"],
    )
    op.create_index("idx_lessons_difficulty", "lessons", ["difficulty"])

    # -----------------------------------------------------------------------
    # 3. student_profiles
    # -----------------------------------------------------------------------
    op.create_table(
        "student_profiles",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("learning_goal", sa.String, nullable=True),
        sa.Column(
            "current_level",
            sa.String(20),
            nullable=False,
            server_default="beginner",
        ),
        sa.Column(
            "preferred_language",
            sa.String(10),
            nullable=False,
            server_default="ru",
        ),
        sa.Column(
            "weekly_study_minutes",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "timezone",
            sa.String(50),
            nullable=False,
            server_default="Asia/Almaty",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "user_id_unique", "student_profiles", ["user_id"]
    )
    op.create_foreign_key(
        "fk_student_profiles_user",
        "student_profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "current_level_check",
        "student_profiles",
        "current_level IN ('beginner', 'intermediate', 'advanced')",
    )
    op.create_check_constraint(
        "weekly_study_minutes_check",
        "student_profiles",
        "weekly_study_minutes >= 0",
    )
    op.create_check_constraint(
        "timezone_not_empty_check",
        "student_profiles",
        "char_length(timezone) > 0",
    )
    op.create_index(
        "idx_student_profiles_current_level",
        "student_profiles",
        ["current_level"],
    )

    # -----------------------------------------------------------------------
    # 4. tasks
    # -----------------------------------------------------------------------
    op.create_table(
        "tasks",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("lesson_id", UUID, nullable=True),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=False),
        sa.Column("instructions", sa.String, nullable=False),
        sa.Column("expected_result_text", sa.String, nullable=True),
        sa.Column("hint", sa.String, nullable=True),
        sa.Column("expected_answer_sql", sa.String, nullable=False),
        sa.Column(
            "validation_strategy",
            sa.String(20),
            nullable=False,
            server_default="exact_match",
        ),
        sa.Column(
            "difficulty", sa.Integer, nullable=False, server_default="1"
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="published",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint("tasks_slug_unique", "tasks", ["slug"])
    op.create_foreign_key(
        "fk_tasks_lesson",
        "tasks",
        "lessons",
        ["lesson_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "validation_strategy_check",
        "tasks",
        "validation_strategy IN ('exact_match', 'sql_result', 'ai', 'manual')",
    )
    op.create_check_constraint(
        "tasks_difficulty_check",
        "tasks",
        "difficulty BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "tasks_status_check",
        "tasks",
        "status IN ('published', 'draft', 'archived')",
    )
    op.create_check_constraint(
        "expected_answer_sql_not_empty_check",
        "tasks",
        "char_length(expected_answer_sql) > 0",
    )
    op.create_index("idx_tasks_lesson_id", "tasks", ["lesson_id"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_difficulty", "tasks", ["difficulty"])

    # -----------------------------------------------------------------------
    # 5. submissions
    # -----------------------------------------------------------------------
    op.create_table(
        "submissions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("task_id", UUID, nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False),
        sa.Column("sql_text", sa.String, nullable=False),
        sa.Column(
            "execution_status",
            sa.String(20),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column("execution_result", JSONB, nullable=True),
        sa.Column("error_text", sa.Text, nullable=True),
        sa.Column("score", sa.Numeric(4, 3), nullable=True),
        sa.Column("feedback", sa.Text, nullable=True),
        sa.Column("is_correct", sa.Boolean, nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_submissions_student",
        "submissions",
        "users",
        ["student_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_submissions_task",
        "submissions",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "attempt_number_positive_check",
        "submissions",
        "attempt_number > 0",
    )
    op.create_check_constraint(
        "score_range_check",
        "submissions",
        "score IS NULL OR (score >= 0 AND score <= 1)",
    )
    op.create_check_constraint(
        "execution_status_check",
        "submissions",
        "execution_status IN ('submitted', 'syntax_error', 'executed', 'reviewed', 'accepted', 'rejected')",
    )
    op.create_check_constraint(
        "sql_text_not_empty_check",
        "submissions",
        "char_length(sql_text) > 0",
    )
    op.create_index(
        "idx_submissions_student_id", "submissions", ["student_id"]
    )
    op.create_index("idx_submissions_task_id", "submissions", ["task_id"])
    op.create_index(
        "idx_submissions_student_task",
        "submissions",
        ["student_id", "task_id"],
    )
    op.create_index(
        "idx_submissions_execution_status",
        "submissions",
        ["execution_status"],
    )
    op.create_index(
        "idx_submissions_is_correct",
        "submissions",
        ["is_correct"],
        postgresql_where=sa.text("is_correct IS NOT NULL"),
    )
    op.create_index(
        "idx_submissions_submitted_at",
        "submissions",
        ["submitted_at"],
    )

    # -----------------------------------------------------------------------
    # 6. lesson_progress
    # -----------------------------------------------------------------------
    op.create_table(
        "lesson_progress",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("lesson_id", UUID, nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "completed_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "student_lesson_unique",
        "lesson_progress",
        ["student_id", "lesson_id"],
    )
    op.create_foreign_key(
        "fk_lesson_progress_student",
        "lesson_progress",
        "users",
        ["student_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_lesson_progress_lesson",
        "lesson_progress",
        "lessons",
        ["lesson_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "lesson_progress_status_check",
        "lesson_progress",
        "status IN ('not_started', 'in_progress', 'completed', 'skipped')",
    )
    op.create_check_constraint(
        "dates_consistency_check",
        "lesson_progress",
        "completed_at IS NULL OR started_at IS NOT NULL",
    )
    op.create_check_constraint(
        "completed_not_before_started_check",
        "lesson_progress",
        "completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at",
    )
    op.create_index(
        "idx_lesson_progress_student_id",
        "lesson_progress",
        ["student_id"],
    )
    op.create_index(
        "idx_lesson_progress_lesson_id",
        "lesson_progress",
        ["lesson_id"],
    )
    op.create_index(
        "idx_lesson_progress_student_status",
        "lesson_progress",
        ["student_id", "status"],
    )
    op.create_index(
        "idx_lesson_progress_status",
        "lesson_progress",
        ["status"],
    )


def downgrade() -> None:
    """Откат: удаляем таблицы в обратном порядке (сначала dependent)."""
    op.drop_table("lesson_progress")
    op.drop_table("submissions")
    op.drop_table("tasks")
    op.drop_table("student_profiles")
    op.drop_table("lessons")
    op.drop_table("users")