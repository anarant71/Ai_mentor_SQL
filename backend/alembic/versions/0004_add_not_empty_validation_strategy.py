"""Add 'not_empty' to validation_strategy check constraint.

Добавляет 'not_empty' как разрешённое значение для validation_strategy
в таблице tasks.

Revision ID: 0004
Revises: 0003_create_mistakes
Create Date: 2026-06-05
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("validation_strategy_check", "tasks", type_="check")
    op.create_check_constraint(
        "validation_strategy_check",
        "tasks",
        "validation_strategy IN ('exact_match', 'sql_result', 'not_empty', 'ai', 'manual')",
    )


def downgrade() -> None:
    op.drop_constraint("validation_strategy_check", "tasks", type_="check")
    op.create_check_constraint(
        "validation_strategy_check",
        "tasks",
        "validation_strategy IN ('exact_match', 'sql_result', 'ai', 'manual')",
    )
