"""Tasks API: /api/v1/tasks/* и /api/v1/lessons/{slug}/tasks."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_platform_session
from app.middleware import require_active
from app.models.user import User
from app.models.skill import Skill, StudentSkill, TaskSkill
from app.schemas.skill import SkillAnalysisResult
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionHistoryItem,
)
from app.schemas.task import TaskListItem, TaskRead
from app.services.ai_skill_analyzer import analyze_skills
from app.services.tasks import (
    create_submission,
    get_submission_history,
    get_task_by_id,
    get_task_with_answer,
    get_tasks_for_lesson,
)
from app.services.validation import validate_submission

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.get(
    "/lessons/{slug}/tasks",
    response_model=list[TaskListItem],
)
async def list_tasks(
    slug: str,
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Список заданий для урока."""
    tasks = await get_tasks_for_lesson(slug, session)
    return [
        TaskListItem(
            id=t.id,
            slug=t.slug,
            title=t.title,
            difficulty=t.difficulty,
            validation_strategy=t.validation_strategy,
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: str,
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Детали задания (без expected_answer_sql)."""
    try:
        tid = UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Задание не найдено",
            },
        )

    task = await get_task_by_id(tid, session)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Задание не найдено",
            },
        )

    return TaskRead.model_validate(task)


@router.get("/tasks")
async def list_all_tasks(
    skill: str | None = Query(None, description="Filter by skill code"),
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Список всех заданий, опционально фильтр по навыку."""
    from app.models.task import Task

    query = select(Task).where(Task.status == "published")
    if skill:
        skill_row = await session.execute(
            select(Skill).where(Skill.code == skill)
        )
        skill_obj = skill_row.scalar_one_or_none()
        if skill_obj is None:
            return []

        query = query.join(TaskSkill, TaskSkill.task_id == Task.id).where(
            TaskSkill.skill_id == skill_obj.id
        )

    query = query.options(
        selectinload(Task.skill_tags).selectinload(TaskSkill.skill)
    )
    result = await session.execute(query)

    tasks = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "slug": t.slug,
            "title": t.title,
            "description": t.description,
            "difficulty": t.difficulty,
            "validation_strategy": t.validation_strategy,
            "skills": [
                {"code": ts.skill.code, "title": ts.skill.title, "weight": float(ts.weight)}
                for ts in t.skill_tags
            ],
        }
        for t in tasks
    ]


@router.post("/tasks/{task_id}/submit")
async def submit_task(
    task_id: str,
    body: SubmissionCreate,
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Отправить SQL-запрос на проверку.

    1. Находит задание (с expected_answer_sql)
    2. Выполняет запрос студента и эталон
    3. Сравнивает результаты
    4. AI-анализ навыков (Nemotron)
    5. Сохраняет попытку + обновляет навыки
    6. Возвращает результат
    """
    try:
        tid = UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Задание не найдено",
            },
        )

    task = await get_task_with_answer(tid, session)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Задание не найдено",
            },
        )

    # Выполнить и сравнить
    try:
        validation = await validate_submission(
            student_sql=body.sql_text,
            expected_sql=task.expected_answer_sql,
            strategy=task.validation_strategy,
        )
    except HTTPException as exc:
        # Ошибка выполнения SQL — сохраняем неудачную попытку
        sub = await create_submission(
            current_user.id, tid, body.sql_text, session
        )
        sub.execution_status = "syntax_error"
        error_message = exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail)
        sub.error_text = error_message
        sub.is_correct = False
        sub.score = 0.0
        sub.reviewed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(sub)
        raise exc

    is_correct = validation["is_correct"]

    # Создаём запись о попытке
    sub = await create_submission(
        current_user.id, tid, body.sql_text, session
    )
    sub.execution_status = "reviewed"
    sub.is_correct = is_correct
    sub.score = 1.0 if is_correct else 0.0
    sub.reviewed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(sub)

    # --- AI Skill Analysis ---
    task_skills_list = await _get_task_skills(tid, session)
    lesson_title = task.lesson.title if task.lesson else ""

    skill_updates = []
    if task_skills_list:
        analysis = await analyze_skills(
            student_sql=body.sql_text,
            expected_sql=task.expected_answer_sql,
            task_skills=task_skills_list,
            is_correct=is_correct,
            attempt_number=sub.attempt_number,
            student_name=current_user.display_name,
            lesson_title=lesson_title,
            task_title=task.title,
        )

        await _update_student_skills(
            current_user.id,
            analysis.get("skill_scores", []),
            session,
        )

        sub.feedback = analysis["feedback"]
        await session.commit()
        await session.refresh(sub)

        skill_updates = [
            {"code": s["code"], "score": s["score"]}
            for s in analysis.get("skill_scores", [])
        ]
    else:
        sub.feedback = (
            "Задание выполнено верно!"
            if is_correct
            else "Есть ошибки в решении."
        )
        await session.commit()
        await session.refresh(sub)

    # --- Mistake detection ---
    if not is_correct:
        from app.services.mistakes import detect_mistakes

        error_text = None
        if task.slug == "syntax_error" and hasattr(sub, 'error_text'):
            error_text = sub.error_text

        skill_code = task_skills_list[0]["code"] if task_skills_list else None

        await detect_mistakes(
            student_id=current_user.id,
            sql_text=body.sql_text,
            is_correct=is_correct,
            session=session,
            skill_code=skill_code,
            submission_id=sub.id,
            error_text=error_text,
        )

    return {
        "submission_id": sub.id if hasattr(sub, 'id') else str(sub.id),
        "attempt_number": sub.attempt_number,
        "is_correct": sub.is_correct,
        "score": float(sub.score) if sub.score else 0.0,
        "feedback": sub.feedback,
        "differences": validation.get("differences", []),
        "skill_updates": skill_updates,
    }


async def _get_task_skills(task_id: UUID, session) -> list[dict]:
    """Получить навыки задания с их весом."""
    result = await session.execute(
        select(TaskSkill)
        .where(TaskSkill.task_id == task_id)
        .options(selectinload(TaskSkill.skill))
    )
    rows = result.scalars().all()
    return [
        {
            "code": ts.skill.code,
            "title": ts.skill.title,
            "weight": float(ts.weight),
        }
        for ts in rows
    ]


async def _update_student_skills(
    student_id: UUID,
    skill_scores: list[dict],
    session,
) -> None:
    """Обновить проценты навыков студента."""
    for ss in skill_scores:
        code = ss["code"]
        score = float(ss["score"])

        skill_row = await session.execute(
            select(Skill).where(Skill.code == code)
        )
        skill_obj = skill_row.scalar_one_or_none()
        if skill_obj is None:
            continue

        result = await session.execute(
            select(StudentSkill)
            .where(
                StudentSkill.student_id == student_id,
                StudentSkill.skill_id == skill_obj.id,
            )
        )
        student_skill = result.scalar_one_or_none()

        if student_skill is None:
            student_skill = StudentSkill(
                student_id=student_id,
                skill_id=skill_obj.id,
                total_attempts=0,
                successful_attempts=0,
                percentage=0,
                confidence=0,
            )
            session.add(student_skill)

        student_skill.total_attempts = (student_skill.total_attempts or 0) + 1
        if score >= 0.7:
            student_skill.successful_attempts = (student_skill.successful_attempts or 0) + 1

        total = max(student_skill.total_attempts, 1)
        successful = student_skill.successful_attempts or 0
        student_skill.confidence = Decimal(
            str(round(successful / total, 2))
        )

        new_pct = Decimal(str(round(score * 100, 2)))
        current_pct = student_skill.percentage or 0
        if new_pct > current_pct:
            student_skill.percentage = new_pct
        elif current_pct == 0:
            student_skill.percentage = new_pct

        student_skill.last_practiced_at = datetime.now(timezone.utc)


@router.get(
    "/tasks/{task_id}/submissions",
    response_model=list[SubmissionHistoryItem],
)
async def list_submissions(
    task_id: str,
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """История попыток студента по заданию."""
    try:
        tid = UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Задание не найдено",
            },
        )

    submissions = await get_submission_history(current_user.id, tid, session)
    return [
        SubmissionHistoryItem(
            attempt_number=s.attempt_number,
            execution_status=s.execution_status,
            is_correct=s.is_correct,
            submitted_at=s.submitted_at,
        )
        for s in submissions
    ]