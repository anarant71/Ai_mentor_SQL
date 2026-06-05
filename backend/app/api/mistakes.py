"""Mistakes API: /api/v1/mistakes/* endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_platform_session
from app.middleware import require_active
from app.models.user import User
from app.schemas.mistake import MistakeTypeRead, StudentMistakeRead
from app.services.mistakes import (
    ensure_mistake_types,
    get_student_mistakes,
    resolve_mistakes,
)

router = APIRouter(prefix="/api/v1/mistakes", tags=["mistakes"])


@router.get("/types", response_model=list[MistakeTypeRead])
async def list_mistake_types(
    session: AsyncSession = Depends(get_platform_session),
):
    """Список всех типов ошибок."""
    from sqlalchemy import select
    from app.models.mistake import MistakeType

    result = await session.execute(
        select(MistakeType).order_by(MistakeType.code)
    )
    return result.scalars().all()


@router.get("", response_model=list[StudentMistakeRead])
async def list_my_mistakes(
    status: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Ошибки текущего студента."""
    mistakes = await get_student_mistakes(
        current_user.id, session, status_filter=status
    )
    result = []
    for m in mistakes:
        result.append(StudentMistakeRead(
            id=m.id,
            mistake_type_id=m.mistake_type_id,
            mistake_code=m.mistake_type.code if m.mistake_type else "",
            mistake_title=m.mistake_type.title if m.mistake_type else "",
            skill_id=m.skill_id,
            title=m.title,
            details=m.details,
            severity=m.severity,
            repeat_count=m.repeat_count,
            status=m.status,
            first_seen_at=m.first_seen_at,
            last_seen_at=m.last_seen_at,
            resolved_at=m.resolved_at,
        ))
    return result


@router.post("/resolve", status_code=status.HTTP_200_OK)
async def resolve_my_mistakes(
    skill_code: str = Query(..., description="Skill code to resolve"),
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Закрыть активные ошибки по навыку."""
    count = await resolve_mistakes(current_user.id, skill_code, session)
    return {"resolved_count": count, "skill_code": skill_code}


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_mistake_types(
    session: AsyncSession = Depends(get_platform_session),
):
    """Создать недостающие типы ошибок (для инициализации)."""
    types = await ensure_mistake_types(session)
    return {"created": len(types), "types": list(types.keys())}