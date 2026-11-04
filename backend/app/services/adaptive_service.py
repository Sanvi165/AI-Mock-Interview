"""Adaptive Follow-up Interview: decide what to ask after each answer."""
from dataclasses import dataclass

STRONG_SCORE = 75.0  # at or above: ask a deeper follow-up
WEAK_SCORE = 40.0    # below: ask a simpler question on the same topic


@dataclass(frozen=True)
class AdaptiveDecision:
    action: str  # "followup" | "simpler" | "next"
    reason: str


def max_adaptive_questions(num_questions: int) -> int:
    """Extra questions allowed per interview, so it cannot go on forever."""
    return max(1, num_questions // 2)


def decide(
    overall_score: float,
    question_kind: str,
    extras_used: int,
    num_questions: int,
) -> AdaptiveDecision:
    if question_kind != "planned":
        return AdaptiveDecision("next", "Moving on to the next planned question.")
    if extras_used >= max_adaptive_questions(num_questions):
        return AdaptiveDecision("next", "Moving on to the next planned question.")
    if overall_score >= STRONG_SCORE:
        return AdaptiveDecision(
            "followup", "Strong answer, so here is a deeper follow-up on the same topic."
        )
    if overall_score < WEAK_SCORE:
        return AdaptiveDecision(
            "simpler", "This looked difficult, so here is a simpler question on the same topic."
        )
    return AdaptiveDecision("next", "Moving on to the next planned question.")