"""Pydantic models for answer evaluation."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RubricScores(BaseModel):
    """Each criterion is scored 0-10."""

    relevance: float = Field(ge=0, le=10)
    correctness: float = Field(ge=0, le=10)
    clarity: float = Field(ge=0, le=10)
    completeness: float = Field(ge=0, le=10)
    problem_solving: float = Field(ge=0, le=10)


class Feedback(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    stronger_answer: str = ""


class CommunicationMetrics(BaseModel):
    """Values MEASURED from the answer text and timer (not AI guesses)."""

    word_count: int
    filler_count: int
    filler_words: dict[str, int] = Field(default_factory=dict)
    words_per_minute: Optional[float] = None
    speech_used: bool = False
    note: str = (
        "Measured from your answer text and timer. Speaking pace is only shown "
        "when the answer was spoken."
    )


class EvaluationOut(BaseModel):
    question_id: int
    scores: RubricScores
    overall_score: float = Field(ge=0, le=100)
    label: str
    feedback: Feedback
    metrics: CommunicationMetrics
    # gemini = AI estimate, demo = rule-based (no API key), fallback = rule-based (AI failed)
    source: Literal["gemini", "demo", "fallback"]
    warning: Optional[str] = None