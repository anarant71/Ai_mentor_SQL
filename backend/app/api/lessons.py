"""Lessons API: /api/v1/lessons/* endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_platform_session
from app.middleware import require_active
from app.models.user import User
from app.schemas.lesson import (
    LessonDetail,
    LessonListItem,
    ProgressUpdateResponse,
)
from app.services.lessons import (
    get_lesson_by_slug,
    get_lessons_with_progress,
    read_lesson_content,
    upsert_progress,
)

router = APIRouter(prefix="/api/v1/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonListItem])
async def list_lessons(
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Список всех опубликованных уроков со статусом пользователя."""
    lessons = await get_lessons_with_progress(current_user.id, session)
    return lessons


@router.get("/{slug}", response_model=LessonDetail)
async def get_lesson(
    slug: str,
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Детали урока + Markdown-контент."""
    lesson = await get_lesson_by_slug(slug, session)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "LESSON_NOT_FOUND",
                "message": "Урок не найден",
            },
        )

    try:
        content = read_lesson_content(lesson.content_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "LESSON_CONTENT_NOT_FOUND",
                "message": "Файл урока не найден на сервере",
            },
        )

    return LessonDetail(
        slug=lesson.slug,
        title=lesson.title,
        module_number=lesson.module_number,
        lesson_number=lesson.lesson_number,
        module_title=lesson.module_title,
        summary=lesson.summary,
        difficulty=lesson.difficulty,
        estimated_minutes=lesson.estimated_minutes,
        content=content,
    )


class ProgressBody(BaseModel):
    status: str = "completed"


@router.post("/{slug}/progress", response_model=ProgressUpdateResponse)
async def update_progress(
    slug: str,
    body: ProgressBody,
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Update lesson progress (in_progress, completed)."""
    lesson = await get_lesson_by_slug(slug, session)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "LESSON_NOT_FOUND",
                "message": "Урок не найден",
            },
        )

    progress = await upsert_progress(
        current_user.id, lesson.id, session, body.status
    )
    return ProgressUpdateResponse(
        status=progress.status,
        message=f"Урок «{lesson.title}» отмечен как «{progress.status}»",
    )