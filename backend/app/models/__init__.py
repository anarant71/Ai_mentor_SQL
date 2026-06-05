"""SQLAlchemy models for AI-Mentor platform."""

from .base import Base, TimestampMixin
from .user import User, StudentProfile
from .lesson import Lesson
from .task import Task
from .submission import Submission
from .progress import LessonProgress
from .skill import Skill, StudentSkill, TaskSkill
from .mistake import MistakeType, StudentMistake
from .roadmap import Roadmap, RoadmapStep, Recommendation

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "StudentProfile",
    "Lesson",
    "Task",
    "Submission",
    "LessonProgress",
    "Skill",
    "StudentSkill",
    "TaskSkill",
    "MistakeType",
    "StudentMistake",
    "Roadmap",
    "RoadmapStep",
    "Recommendation",
]