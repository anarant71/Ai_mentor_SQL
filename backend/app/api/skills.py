"""Skills API: /api/v1/skills/* endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_platform_session
from app.middleware import require_active
from app.models.user import User
from app.models.skill import Skill, StudentSkill
from app.schemas.skill import SkillRead, StudentSkillRead

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.get("", response_model=list[SkillRead])
async def list_skills(
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Список всех активных навыков."""
    result = await session.execute(
        select(Skill)
        .where(Skill.is_active == True)
        .order_by(Skill.sort_order)
    )
    return result.scalars().all()


@router.get("/student", response_model=list[StudentSkillRead])
async def student_skills(
    current_user: User = Depends(require_active),
    session: AsyncSession = Depends(get_platform_session),
):
    """Навыки текущего студента с процентами.

    Один запрос: LEFT JOIN student_skills -> все активные навыки.
    """
    from sqlalchemy import literal, Integer
    from sqlalchemy.orm import aliased

    result = await session.execute(
        select(
            Skill,
            StudentSkill.percentage,
            StudentSkill.confidence,
            StudentSkill.total_attempts,
            StudentSkill.successful_attempts,
            StudentSkill.last_practiced_at,
        )
        .outerjoin(
            StudentSkill,
            and_(
                StudentSkill.skill_id == Skill.id,
                StudentSkill.student_id == current_user.id,
            ),
        )
        .where(Skill.is_active == True)
        .order_by(Skill.sort_order)
    )

    rows = []
    for skill, pct, conf, total, successful, last_practiced in result:
        rows.append(StudentSkillRead(
            skill_id=skill.id,
            skill_code=skill.code,
            skill_title=skill.title,
            skill_icon=skill.icon,
            skill_category=skill.category,
            percentage=pct if pct is not None else 0,
            confidence=conf if conf is not None else 0,
            total_attempts=total if total is not None else 0,
            successful_attempts=successful if successful is not None else 0,
            last_practiced_at=last_practiced,
        ))

    return sorted(rows, key=lambda x: x.skill_code)