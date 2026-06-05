from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RoadmapRead(BaseModel):
    id: UUID
    student_id: UUID
    title: str
    goal: Optional[str] = None
    status: str
    source: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RoadmapStepRead(BaseModel):
    id: UUID
    roadmap_id: UUID
    position: int
    step_type: str
    lesson_id: Optional[UUID] = None
    skill_id: Optional[UUID] = None
    title: str
    reason: Optional[str] = None
    status: str
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoadmapWithSteps(RoadmapRead):
    steps: list[RoadmapStepRead] = []


class RecommendationRead(BaseModel):
    id: UUID
    student_id: UUID
    rec_type: str
    title: str
    description: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    reason: Optional[str] = None
    priority: int
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RecommendationAction(BaseModel):
    action: str  # "accept", "dismiss", "complete"