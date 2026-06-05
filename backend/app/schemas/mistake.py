from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MistakeTypeRead(BaseModel):
    id: UUID
    code: str
    title: str
    description: Optional[str] = None
    domain: str
    severity_default: int

    model_config = {"from_attributes": True}


class StudentMistakeRead(BaseModel):
    id: UUID
    mistake_type_id: UUID
    mistake_code: str = ""
    mistake_title: str = ""
    skill_id: Optional[UUID] = None
    title: str
    details: Optional[str] = None
    severity: int
    repeat_count: int
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MistakeDetectionInput(BaseModel):
    student_id: UUID
    skill_code: Optional[str] = None
    submission_id: Optional[UUID] = None
    sql_text: str
    is_correct: bool
    differences: list[str] = []