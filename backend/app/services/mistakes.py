"""Mistakes service — обнаружение и управление типовыми ошибками."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mistake import MistakeType, StudentMistake


# Простые правила обнаружения ошибок по тексту SQL
_MISTAKE_PATTERNS = [
    {
        "code": "missing_where",
        "title": "Отсутствует WHERE",
        "domain": "sql",
        "severity": 3,
        "keywords": ["select", "delete", "update"],
        "check": lambda sql: (
            any(sql.lower().strip().startswith(kw) for kw in ["select", "delete", "update"])
            and "where" not in sql.lower()
        ),
    },
    {
        "code": "select_star",
        "title": "SELECT * вместо конкретных колонок",
        "domain": "sql",
        "severity": 1,
        "check": lambda sql: (
            "select *" in sql.lower()
            or sql.lower().strip().startswith("select *")
        ),
    },
    {
        "code": "missing_join_condition",
        "title": "JOIN без ON",
        "domain": "sql",
        "severity": 4,
        "check": lambda sql: (
            "join" in sql.lower()
            and " on " not in sql.lower()
            and " using " not in sql.lower()
        ),
    },
    {
        "code": "typo_in_column",
        "title": "Опечатка в имени колонки или таблицы",
        "domain": "sql",
        "severity": 2,
        "check": lambda sql: False,  # определяется по ошибке БД
    },
]


async def ensure_mistake_types(session: AsyncSession) -> dict[str, UUID]:
    """Создать недостающие типы ошибок, вернуть mapping code->id."""
    result = {}
    for pattern in _MISTAKE_PATTERNS:
        existing = await session.execute(
            select(MistakeType).where(MistakeType.code == pattern["code"])
        )
        mt = existing.scalar_one_or_none()
        if mt is None:
            mt = MistakeType(
                code=pattern["code"],
                title=pattern["title"],
                domain=pattern["domain"],
                severity_default=pattern["severity"],
            )
            session.add(mt)
            await session.flush()
        result[pattern["code"]] = mt.id
    return result


async def detect_mistakes(
    student_id: UUID,
    sql_text: str,
    is_correct: bool,
    session: AsyncSession,
    skill_code: Optional[str] = None,
    submission_id: Optional[UUID] = None,
    error_text: Optional[str] = None,
) -> list[StudentMistake]:
    """Обнаружить типовые ошибки в SQL-запросе и сохранить/обновить их.

    Returns:
        Список созданных или обновлённых StudentMistake.
    """
    from app.models.skill import Skill

    now = datetime.now(timezone.utc)
    detected = []

    # Определяем skill_id, если передан skill_code
    skill_id = None
    if skill_code:
        skill_row = await session.execute(
            select(Skill).where(Skill.code == skill_code)
        )
        skill_obj = skill_row.scalar_one_or_none()
        if skill_obj:
            skill_id = skill_obj.id

    for pattern in _MISTAKE_PATTERNS:
        if not pattern["check"](sql_text):
            # Для typo_in_column проверяем error_text
            if pattern["code"] != "typo_in_column" or not error_text:
                continue
            # Определяем опечатку по тексту ошибки
            if "does not exist" not in error_text.lower() and "syntax error" not in error_text.lower():
                continue

        # Ошибка обнаружена — ищем существующую
        mistake_type_id = await _get_or_create_type(pattern, session)

        existing = await session.execute(
            select(StudentMistake).where(
                StudentMistake.student_id == student_id,
                StudentMistake.mistake_type_id == mistake_type_id,
                StudentMistake.status.in_(["new", "active", "training"]),
            )
        )
        mistake = existing.scalar_one_or_none()

        if mistake:
            mistake.repeat_count = (mistake.repeat_count or 0) + 1
            mistake.last_seen_at = now
            mistake.severity = min(mistake.severity + 1, 5)
            if mistake.repeat_count >= 3:
                mistake.status = "active"
            if mistake.repeat_count >= 5:
                mistake.status = "training"
        else:
            mistake = StudentMistake(
                student_id=student_id,
                mistake_type_id=mistake_type_id,
                skill_id=skill_id,
                submission_id=submission_id,
                title=pattern["title"],
                severity=pattern["severity"],
                repeat_count=1,
                status="new",
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(mistake)

        detected.append(mistake)

    await session.commit()
    return detected


async def _get_or_create_type(pattern: dict, session: AsyncSession) -> UUID:
    """Найти или создать MistakeType."""
    existing = await session.execute(
        select(MistakeType).where(MistakeType.code == pattern["code"])
    )
    mt = existing.scalar_one_or_none()
    if mt is not None:
        return mt.id

    mt = MistakeType(
        code=pattern["code"],
        title=pattern["title"],
        domain=pattern.get("domain", "sql"),
        severity_default=pattern.get("severity", 2),
    )
    session.add(mt)
    await session.flush()
    return mt.id


async def get_student_mistakes(
    student_id: UUID,
    session: AsyncSession,
    status_filter: Optional[str] = None,
) -> list[StudentMistake]:
    """Получить ошибки студента."""
    query = (
        select(StudentMistake)
        .where(StudentMistake.student_id == student_id)
        .order_by(StudentMistake.last_seen_at.desc())
    )
    if status_filter:
        query = query.where(StudentMistake.status == status_filter)

    result = await session.execute(query)
    return list(result.scalars().all())


async def resolve_mistakes(
    student_id: UUID,
    skill_code: str,
    session: AsyncSession,
) -> int:
    """Закрыть активные ошибки по навыку (после успешной серии)."""
    from app.models.skill import Skill

    skill_row = await session.execute(
        select(Skill).where(Skill.code == skill_code)
    )
    skill_obj = skill_row.scalar_one_or_none()
    if skill_obj is None:
        return 0

    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(StudentMistake).where(
            StudentMistake.student_id == student_id,
            StudentMistake.skill_id == skill_obj.id,
            StudentMistake.status.in_(["new", "active", "training"]),
        )
    )
    count = 0
    for mistake in result.scalars().all():
        mistake.status = "resolved"
        mistake.resolved_at = now
        count += 1

    await session.commit()
    return count