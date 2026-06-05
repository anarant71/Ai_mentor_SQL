"""Create skills, student_skills, task_skills tables.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="basic"),
        sa.Column("icon", sa.String(10), nullable=False, server_default="📋"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "student_skills",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", UUID, sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="0.00"),
        sa.Column("total_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("successful_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_practiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "task_skills",
        sa.Column("task_id", UUID, sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", UUID, sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("weight", sa.Numeric(3, 2), nullable=False, server_default="1.00"),
    )

    op.create_index("idx_student_skills_student", "student_skills", ["student_id"])
    op.create_index("idx_student_skills_skill", "student_skills", ["skill_id"])
    op.create_index("uq_student_skills", "student_skills", ["student_id", "skill_id"], unique=True)
    op.create_index("idx_task_skills_task", "task_skills", ["task_id"])
    op.create_index("idx_task_skills_skill", "task_skills", ["skill_id"])

    # Seed 10 standard skills
    skills_data = [
        ("select_basic", "Базовый SELECT", "Выбор данных из таблиц: SELECT, *, явные колонки", "basic", "📋", 1),
        ("where_filter", "Фильтрация WHERE", "Условия отбора строк: =, <>, >, <, AND, OR, IN", "basic", "🔍", 2),
        ("order_limit", "Сортировка и LIMIT", "Упорядочивание результатов: ORDER BY, LIMIT, OFFSET", "basic", "📊", 3),
        ("group_by", "Агрегация GROUP BY", "Группировка и агрегатные функции: SUM, COUNT, AVG, MIN, MAX", "intermediate", "📈", 4),
        ("join", "JOIN", "Соединение таблиц: INNER JOIN, LEFT JOIN, RIGHT JOIN", "intermediate", "🔗", 5),
        ("subqueries", "Подзапросы", "Вложенные запросы: WHERE IN (SELECT ...)", "advanced", "🪆", 6),
        ("window_func", "Оконные функции", "Оконные функции: ROW_NUMBER, RANK, OVER, PARTITION BY", "advanced", "🪟", 7),
        ("cte", "CTE", "Common Table Expressions: WITH ... AS", "advanced", "📝", 8),
        ("null_types", "NULL и типы данных", "Работа с NULL и приведение типов: COALESCE, NULLIF, CAST", "intermediate", "❓", 9),
        ("date_func", "Работа с датами", "Функции даты и времени: DATE_TRUNC, EXTRACT, INTERVAL", "intermediate", "📅", 10),
    ]
    for code, title, desc, cat, icon, order in skills_data:
        op.execute(
            f"INSERT INTO skills (code, title, description, category, icon, sort_order) "
            f"VALUES ('{code}', '{title}', '{desc}', '{cat}', '{icon}', {order}) "
            f"ON CONFLICT (code) DO NOTHING;"
        )


def downgrade() -> None:
    op.drop_table("task_skills")
    op.drop_table("student_skills")
    op.drop_table("skills")