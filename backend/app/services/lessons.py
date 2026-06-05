"""Lessons service: получение уроков, чтение Markdown, управление прогрессом."""

import functools
import os
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.roadmap import Roadmap, RoadmapStep


async def get_lessons_with_progress(
    user_id: UUID,
    session: AsyncSession,
) -> list[dict]:
    """
    Вернуть все опубликованные уроки со статусом пользователя
    и статусом roadmap (locked/available/completed).

    LEFT JOIN lesson_progress -> status или "not_started" если записи нет.
    LEFT JOIN roadmap_steps -> roadmap_status или None если roadmap нет.
    """
    # Достаём активный roadmap пользователя
    roadmap = await _get_active_roadmap(user_id, session)

    query = (
        select(Lesson, LessonProgress.status)
        .outerjoin(
            LessonProgress,
            and_(
                LessonProgress.lesson_id == Lesson.id,
                LessonProgress.student_id == user_id,
            ),
        )
        .where(Lesson.status == "published")
        .order_by(Lesson.module_number, Lesson.lesson_number)
    )
    result = await session.execute(query)

    # Строим map lesson_id -> roadmap_status (если roadmap есть)
    step_map: dict[UUID, str] = {}
    if roadmap and roadmap.steps:
        for step in roadmap.steps:
            if step.lesson_id:
                step_map[step.lesson_id] = step.status

    rows = []
    for lesson, progress_status in result:
        rows.append(
            {
                "slug": lesson.slug,
                "title": lesson.title,
                "module_number": lesson.module_number,
                "lesson_number": lesson.lesson_number,
                "module_title": lesson.module_title,
                "difficulty": lesson.difficulty,
                "estimated_minutes": lesson.estimated_minutes,
                "status": progress_status or "not_started",
                "roadmap_status": step_map.get(lesson.id),
            }
        )
    return rows


async def _get_active_roadmap(
    user_id: UUID,
    session: AsyncSession,
) -> Roadmap | None:
    """Получить активный roadmap пользователя с шагами (загрузка одной выборкой)."""
    result = await session.execute(
        select(Roadmap)
        .where(
            Roadmap.student_id == user_id,
            Roadmap.status == "active",
        )
        .options(selectinload(Roadmap.steps))
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_lesson_roadmap_status(
    user_id: UUID,
    lesson_id: UUID,
    session: AsyncSession,
) -> str | None:
    """Вернуть roadmap_status для конкретного урока."""
    roadmap = await _get_active_roadmap(user_id, session)
    if roadmap is None:
        return None
    for step in roadmap.steps:
        if step.lesson_id == lesson_id:
            return step.status
    return None


async def get_lesson_by_slug(
    slug: str,
    session: AsyncSession,
) -> Lesson | None:
    """Найти урок по slug."""
    query = select(Lesson).where(Lesson.slug == slug)
    result = await session.execute(query)
    return result.scalar_one_or_none()


def _read_lesson_file(filepath: str) -> str:
    """Прочитать Markdown-файл с диска."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Lesson file not found: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        return f.read()


@functools.lru_cache(maxsize=32)
def read_lesson_content(content_path: str) -> str:
    """Прочитать Markdown-файл урока с кэшированием (LRU, 32 файла).

    Аргумент content_path может быть 'lesson_01.md' или 'lessons/lesson_01.md'.
    Кэш сбрасывается при перезапуске сервера.
    """
    filename = os.path.basename(content_path)
    filepath = os.path.join(settings.LESSONS_DIR, filename)

    return _read_lesson_file(filepath)


async def upsert_progress(
    user_id: UUID,
    lesson_id: UUID,
    session: AsyncSession,
    new_status: str = "completed",
) -> LessonProgress:
    """Создать или обновить запись прогресса (upsert по student_lesson_unique).

    При первом завершении проставляет started_at / completed_at.
    Повторный вызов не создаёт дубликат.
    Не даёт завершить locked-урок.
    """
    # Проверяем roadmap — нельзя завершить locked-урок
    if new_status == "completed":
        rstatus = await get_lesson_roadmap_status(user_id, lesson_id, session)
        if rstatus == "locked":
            raise PermissionError("Lesson is locked — complete previous lessons first")

    query = select(LessonProgress).where(
        LessonProgress.student_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    )
    result = await session.execute(query)
    progress = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if progress is not None:
        # Bugfix: не понижать completed -> in_progress
        if progress.status == "completed" and new_status == "in_progress":
            return progress

        old_status = progress.status
        progress.status = new_status
        if new_status == "completed" and old_status != "completed":
            progress.completed_at = now
        if new_status == "in_progress" and progress.started_at is None:
            progress.started_at = now
    else:
        progress = LessonProgress(
            student_id=user_id,
            lesson_id=lesson_id,
            status=new_status,
            started_at=now if new_status in ("in_progress", "completed") else None,
            completed_at=now if new_status == "completed" else None,
        )
        session.add(progress)

    await session.commit()
    await session.refresh(progress)
    return progress
