"""Pydantic models for interview sessions, questions and answers."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.evaluation import EvaluationOut

ExperienceLevel = Literal["Fresher", "Junior", "Mid-level", "Senior"]
InterviewType = Literal["Technical", "HR", "Situational", "Mixed", "Aptitude", "GD"]
QuestionKind = Literal["planned", "followup", "simpler"]
AISource = Literal["gemini", "demo", "fallback"]


class InterviewSetupRequest(BaseModel):
    role: str = Field(min_length=2, max_length=100)
    domain: str = Field(default="", max_length=100)
    experience_level: ExperienceLevel
    interview_type: InterviewType
    num_questions: int = Field(default=5, ge=1, le=10)

    @field_validator("role", "domain", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class QuestionOut(BaseModel):
    id: int
    position: int
    text: str
    topic: str
    difficulty: str
    kind: QuestionKind = "planned"
    answered: bool = False
    # Only multiple-choice (Aptitude) questions have options. The correct answer is never sent here.
    options: Optional[list[str]] = None


class SessionBase(BaseModel):
    id: int
    role: str
    domain: str
    experience_level: str
    interview_type: str
    num_questions: int
    status: str
    ai_source: AISource
    overall_score: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None
    question_count: int = 0
    answered_count: int = 0


class SessionOut(SessionBase):
    questions: list[QuestionOut] = Field(default_factory=list)
    warning: Optional[str] = None


class AnswerRequest(BaseModel):
    question_id: int = Field(ge=1)
    answer_text: str
    time_taken_seconds: int = Field(default=0, ge=0, le=7200)
    speech_used: bool = False

    @field_validator("answer_text")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Answer cannot be empty. Type or speak your answer first.")
        if len(value) > 5000:
            raise ValueError("Answer is too long (maximum 5000 characters).")
        return value


class McqResult(BaseModel):
    """Result of a multiple-choice (Aptitude) answer."""

    is_correct: bool
    chosen: str            # for example "B) 120 km"
    correct_option: str    # the letter, for example "C"
    correct_text: str      # for example "C) 150 km"
    quick: str             # one short sentence (shown when the answer is right)
    explanation: str       # full working (shown when the answer is wrong)


class AnswerResponse(BaseModel):
    evaluation: EvaluationOut
    mcq: Optional[McqResult] = None
    adaptive_action: Literal["followup", "simpler", "next", "finish"]
    adaptive_reason: str
    next_question: Optional[QuestionOut] = None
    answered_count: int
    question_count: int


class QuestionResult(BaseModel):
    question: QuestionOut
    answer_text: Optional[str] = None
    time_taken_seconds: Optional[int] = None
    evaluation: Optional[EvaluationOut] = None


class SessionSummary(BaseModel):
    answered: int
    total_questions: int
    criterion_averages: dict[str, float]
    strong_topics: list[str]
    weak_topics: list[str]


class SessionDetail(SessionBase):
    results: list[QuestionResult] = Field(default_factory=list)
    summary: Optional[SessionSummary] = None