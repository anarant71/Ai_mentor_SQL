"""Submission schemas: отправка, чтение, история."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SubmissionCreate(BaseModel):
    sql_text: str


class SubmissionRead(BaseModel):
    id: UUID
    task_id: UUID
    attempt_number: int
    execution_status: str
    score: Decimal | None = None
    feedback: str | None = None
    is_correct: bool | None = None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class SubmissionHistoryItem(BaseModel):
    attempt_number: int
    execution_status: str
    is_correct: bool | None = None
    submitted_at: datetime