"""Task schemas: список заданий, детали задания."""

from uuid import UUID

from pydantic import BaseModel


class TaskListItem(BaseModel):
    id: UUID
    slug: str
    title: str
    difficulty: int
    validation_strategy: str


class TaskRead(BaseModel):
    """Детали задания — без expected_answer_sql."""

    id: UUID
    lesson_id: UUID
    slug: str
    title: str
    description: str
    instructions: str
    expected_result_text: str | None = None
    hint: str | None = None
    difficulty: int
    validation_strategy: str

    model_config = {"from_attributes": True}