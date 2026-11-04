import pytest

from app.demo import sample_data
from app.services import adaptive_service, evaluation_service


def test_weights_sum_to_one():
    assert sum(evaluation_service.WEIGHTS.values()) == pytest.approx(1.0)


def test_overall_score_bounds():
    perfect = {c: 10 for c in evaluation_service.CRITERIA}
    zero = {c: 0 for c in evaluation_service.CRITERIA}
    assert evaluation_service.calculate_overall(perfect) == 100.0
    assert evaluation_service.calculate_overall(zero) == 0.0


def test_score_labels():
    assert evaluation_service.score_label(85) == "Excellent"
    assert evaluation_service.score_label(65) == "Good"
    assert evaluation_service.score_label(45) == "Needs work"
    assert evaluation_service.score_label(10) == "Weak"


def test_metrics_count_fillers_and_pace_only_for_speech():
    text = "Um, basically I think, you know, it works. Actually it is simple."
    typed = evaluation_service.compute_metrics(text, 30, speech_used=False)
    spoken = evaluation_service.compute_metrics(text, 30, speech_used=True)
    assert typed.filler_count >= 4
    assert typed.words_per_minute is None
    assert spoken.words_per_minute is not None and spoken.words_per_minute > 0


def test_validate_ai_evaluation_clamps_scores():
    data = {
        "scores": {c: 15 for c in evaluation_service.CRITERIA},
        "feedback": {"strengths": ["good"], "stronger_answer": "model"},
    }
    cleaned = evaluation_service.validate_ai_evaluation(data)
    assert all(score == 10.0 for score in cleaned["scores"].values())
    assert cleaned["feedback"]["weaknesses"] == []


def test_validate_ai_evaluation_rejects_missing_criterion():
    data = {"scores": {"relevance": 5}, "feedback": {}}
    with pytest.raises(ValueError):
        evaluation_service.validate_ai_evaluation(data)


def test_heuristic_strong_answer_beats_weak_answer():
    entry = sample_data.QUESTION_BANK[0]
    question = {"text": entry["text"], "topic": entry["topic"]}
    strong = evaluation_service.heuristic_evaluate(question, entry["model_answer"])
    weak = evaluation_service.heuristic_evaluate(question, "I do not know.")
    assert evaluation_service.calculate_overall(strong["scores"]) > evaluation_service.calculate_overall(
        weak["scores"]
    )
    assert weak["feedback"]["missing_concepts"]


def test_adaptive_rules():
    decide = adaptive_service.decide
    assert decide(80, "planned", 0, 5).action == "followup"
    assert decide(30, "planned", 0, 5).action == "simpler"
    assert decide(55, "planned", 0, 5).action == "next"
    # No chaining: a follow-up never produces another follow-up.
    assert decide(90, "followup", 0, 5).action == "next"
    # Cap on extra questions (5 questions -> at most 2 extras).
    assert decide(90, "planned", 2, 5).action == "next"