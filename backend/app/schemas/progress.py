"""Pydantic models for progress analytics and the skill gap roadmap."""
from typing import Optional

from pydantic import BaseModel, Field


class SessionPoint(BaseModel):
    session_id: int
    label: str
    role: str
    overall_score: float


class TopicPerformance(BaseModel):
    topic: str
    average_score: float
    attempts: int


class ProgressOut(BaseModel):
    total_sessions: int
    completed_sessions: int
    total_answers: int
    average_score: Optional[float] = None
    best_score: Optional[float] = None
    latest_score: Optional[float] = None
    improvement: Optional[float] = None
    strongest_topic: Optional[str] = None
    weakest_topic: Optional[str] = None
    sessions: list[SessionPoint] = Field(default_factory=list)
    topics: list[TopicPerformance] = Field(default_factory=list)


class RoadmapItem(BaseModel):
    topic: str
    priority: int
    urgency: str
    average_score: float
    attempts: int
    reason: str
    study_focus: list[str]
    practice_questions: list[str]


class RoadmapOut(BaseModel):
    items: list[RoadmapItem] = Field(default_factory=list)
    generated_from_answers: int = 0
    message: Optional[str] = None