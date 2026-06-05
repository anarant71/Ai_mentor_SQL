"""Tasks service: получение заданий, создание попыток."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lesson import Lesson
from app.models.submission import Submission
from app.models.task import Task


async def get_tasks_for_lesson(
    slug: str,
    session: AsyncSession,
) -> list[Task]:
    """Найти урок по slug, вернуть его задания."""
    lesson_query = select(Lesson).where(Lesson.slug == slug)
    lesson_result = await session.execute(lesson_query)
    lesson = lesson_result.scalar_one_or_none()

    if lesson is None:
        return []

    tasks_query = (
        select(Task)
        .where(Task.lesson_id == lesson.id, Task.status == "published")
        .order_by(Task.slug)
    )
    tasks_result = await session.execute(tasks_query)
    return list(tasks_result.scalars().all())


async def get_task_by_id(task_id: UUID, session: AsyncSession) -> Task | None:
    """Найти задание по id (без expected_answer_sql — для API)."""
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def get_task_with_answer(
    task_id: UUID,
    session: AsyncSession,
) -> Task | None:
    """Найти задание со всеми полями, включая expected_answer_sql.

    Только для внутреннего использования (валидация).
    """
    result = await session.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.lesson))
    )
    return result.scalar_one_or_none()


async def create_submission(
    student_id: UUID,
    task_id: UUID,
    sql_text: str,
    session: AsyncSession,
) -> Submission:
    """Создать попытку. attempt_number = max + 1."""
    max_result = await session.execute(
        select(func.max(Submission.attempt_number)).where(
            Submission.student_id == student_id,
            Submission.task_id == task_id,
        )
    )
    max_attempt = max_result.scalar() or 0

    submission = Submission(
        student_id=student_id,
        task_id=task_id,
        attempt_number=max_attempt + 1,
        sql_text=sql_text,
        execution_status="submitted",
    )
    session.add(submission)
    await session.commit()
    await session.refresh(submission)
    return submission


async def get_submission_history(
    student_id: UUID,
    task_id: UUID,
    session: AsyncSession,
) -> list[Submission]:
    """История попыток студента по заданию."""
    query = (
        select(Submission)
        .where(
            Submission.student_id == student_id,
            Submission.task_id == task_id,
        )
        .order_by(Submission.submitted_at.desc())
    )
    result = await session.execute(query)
    return list(result.scalars().all())