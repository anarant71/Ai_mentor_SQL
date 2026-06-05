"""Roadmap and Recommendations services."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lesson import Lesson
from app.models.roadmap import Roadmap, RoadmapStep, Recommendation
from app.models.skill import Skill


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

async def create_default_roadmap(
    student_id: UUID,
    session: AsyncSession,
) -> Roadmap:
    """Создать дефолтный roadmap для нового студента на основе всех уроков."""
    roadmap = Roadmap(
        student_id=student_id,
        title="Базовый курс SQL",
        goal="Освоить основы SQL на учебной БД мебельной фабрики",
        status="active",
        source="automatic",
        started_at=datetime.now(timezone.utc),
    )
    session.add(roadmap)
    await session.flush()

    # Получаем все опубликованные уроки
    lessons_result = await session.execute(
        select(Lesson)
        .where(Lesson.status == "published")
        .order_by(Lesson.module_number, Lesson.lesson_number)
    )
    lessons = list(lessons_result.scalars().all())

    for i, lesson in enumerate(lessons, start=1):
        step = RoadmapStep(
            roadmap_id=roadmap.id,
            position=i,
            step_type="lesson",
            lesson_id=lesson.id,
            title=f"{lesson.module_title}: {lesson.title}",
            reason="Последовательное изучение SQL",
            status="available" if i == 1 else "locked",
        )
        session.add(step)

    await session.commit()
    await session.refresh(roadmap)
    return roadmap


async def get_active_roadmap(
    student_id: UUID,
    session: AsyncSession,
) -> Optional[Roadmap]:
    """Получить активный roadmap студента со всеми шагами."""
    result = await session.execute(
        select(Roadmap)
        .where(
            Roadmap.student_id == student_id,
            Roadmap.status == "active",
        )
        .options(selectinload(Roadmap.steps))
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def advance_roadmap_step(
    student_id: UUID,
    lesson_slug: str,
    session: AsyncSession,
) -> Optional[RoadmapStep]:
    """Отметить шаг roadmap как выполненный и разблокировать следующий."""
    from app.models.lesson import Lesson

    roadmap = await get_active_roadmap(student_id, session)
    if roadmap is None:
        return None

    # Найти шаг по уроку
    lesson_result = await session.execute(
        select(Lesson).where(Lesson.slug == lesson_slug)
    )
    lesson = lesson_result.scalar_one_or_none()
    if lesson is None:
        return None

    # Ищем соответствующий шаг в roadmap
    step_result = await session.execute(
        select(RoadmapStep).where(
            RoadmapStep.roadmap_id == roadmap.id,
            RoadmapStep.lesson_id == lesson.id,
        )
    )
    step = step_result.scalar_one_or_none()
    if step is None:
        return None

    now = datetime.now(timezone.utc)
    step.status = "completed"
    step.completed_at = now

    # Разблокировать следующий шаг
    next_step_result = await session.execute(
        select(RoadmapStep).where(
            RoadmapStep.roadmap_id == roadmap.id,
            RoadmapStep.position == step.position + 1,
            RoadmapStep.status == "locked",
        )
    )
    next_step = next_step_result.scalar_one_or_none()
    if next_step:
        next_step.status = "available"

    # Проверяем, все ли шаги выполнены
    remaining = await session.execute(
        select(func.count(RoadmapStep.id)).where(
            RoadmapStep.roadmap_id == roadmap.id,
            RoadmapStep.status != "completed",
        )
    )
    if remaining.scalar() == 0:
        roadmap.status = "completed"
        roadmap.completed_at = now

    await session.commit()
    await session.refresh(step)
    return step


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

async def create_recommendation(
    student_id: UUID,
    rec_type: str,
    title: str,
    session: AsyncSession,
    description: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[UUID] = None,
    reason: Optional[str] = None,
    priority: int = 0,
) -> Recommendation:
    """Создать рекомендацию для студента."""
    rec = Recommendation(
        student_id=student_id,
        rec_type=rec_type,
        title=title,
        description=description,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        priority=priority,
        status="new",
    )
    session.add(rec)
    await session.commit()
    await session.refresh(rec)
    return rec


async def get_student_recommendations(
    student_id: UUID,
    session: AsyncSession,
    status_filter: Optional[str] = "new",
) -> list[Recommendation]:
    """Получить рекомендации студента."""
    query = (
        select(Recommendation)
        .where(Recommendation.student_id == student_id)
        .order_by(Recommendation.priority.desc(), Recommendation.created_at.desc())
    )
    if status_filter:
        query = query.where(Recommendation.status == status_filter)

    result = await session.execute(query)
    return list(result.scalars().all())


async def update_recommendation_status(
    rec_id: UUID,
    action: str,
    session: AsyncSession,
) -> Optional[Recommendation]:
    """Обновить статус рекомендации."""
    result = await session.execute(
        select(Recommendation).where(Recommendation.id == rec_id)
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        return None

    status_map = {
        "accept": "accepted",
        "dismiss": "dismissed",
        "complete": "completed",
    }
    rec.status = status_map.get(action, rec.status)
    await session.commit()
    await session.refresh(rec)
    return rec


async def generate_recommendations_after_submit(
    student_id: UUID,
    is_correct: bool,
    session: AsyncSession,
    skill_codes: list[str] | None = None,
) -> list[Recommendation]:
    """Сгенерировать рекомендации после отправки задания."""
    created = []

    if not is_correct and skill_codes:
        # Рекомендуем повторить слабые навыки
        for code in skill_codes:
            rec = await create_recommendation(
                student_id=student_id,
                rec_type="practice",
                title=f"Повтори навык: {code}",
                description=f"У тебя были ошибки по навыку {code}. Попробуй ещё раз.",
                reason="Ошибки в задании",
                priority=3,
            )
            created.append(rec)

    # Рекомендация следующего урока — генерируется отдельно через roadmap

    return created