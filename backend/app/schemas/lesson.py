"""Lesson schemas: список, детали, прогресс."""

from pydantic import BaseModel


class LessonListItem(BaseModel):
    slug: str
    title: str
    module_number: int
    lesson_number: int
    module_title: str
    difficulty: int
    estimated_minutes: int
    status: str  # "not_started" | "in_progress" | "completed" | "skipped"
    roadmap_status: str | None = None  # "locked" | "available" | "completed"


class LessonDetail(BaseModel):
    slug: str
    title: str
    module_number: int
    lesson_number: int
    module_title: str
    summary: str
    difficulty: int
    estimated_minutes: int
    content: str  # Markdown-текст
    roadmap_status: str | None = None


class ProgressUpdateResponse(BaseModel):
    status: str
    message: str