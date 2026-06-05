"""Pydantic schemas for skills."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SkillRead(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    description: Optional[str] = None
    category: str
    icon: str
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class StudentSkillRead(BaseModel):
    skill_id: uuid.UUID
    skill_code: str
    skill_title: str
    skill_icon: str
    skill_category: str
    percentage: Decimal
    confidence: Decimal
    total_attempts: int
    successful_attempts: int
    last_practiced_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SkillAnalysisResult(BaseModel):
    code: str
    score: Decimal
    comment: str


class SkillSubmitEnhancement(BaseModel):
    skill_updates: list[SkillAnalysisResult]
    feedback: str
    weak_areas: list[str]
    next_focus: Optional[str] = None