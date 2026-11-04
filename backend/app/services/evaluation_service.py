"""Rubric, score maths, rule-based evaluation, metrics and session summaries.

Everything here is pure logic (no network, no database), so it is easy to test.
"""
import json
import re
from collections import Counter
from typing import Any

from app.demo import sample_data
from app.schemas.evaluation import (
    CommunicationMetrics,
    EvaluationOut,
    Feedback,
    RubricScores,
)
from app.schemas.interview import (
    QuestionOut,
    QuestionResult,
    SessionDetail,
    SessionSummary,
)

CRITERIA = ("relevance", "correctness", "clarity", "completeness", "problem_solving")

# Weights sum to 1.0. Correctness matters most.
WEIGHTS = {
    "relevance": 0.25,
    "correctness": 0.30,
    "clarity": 0.15,
    "completeness": 0.15,
    "problem_solving": 0.15,
}

WEAK_TOPIC_THRESHOLD = 70.0
STRONG_TOPIC_THRESHOLD = 75.0

FILLER_PATTERN = re.compile(
    r"\b(um+|uh+|erm|hmm|you know|i mean|basically|actually|literally|kind of|sort of)\b",
    re.IGNORECASE,
)
REASONING_MARKERS = (
    "because", "therefore", "for example", "for instance", "first", "then",
    "so that", "in order to", "trade-off", "tradeoff", "however", "approach", "step",
)
STOPWORDS = {
    "what", "which", "where", "when", "does", "about", "would", "explain", "describe",
    "difference", "between", "example", "should", "could", "there", "their", "these",
    "those", "while", "using", "give", "tell", "your", "have", "with", "from", "that",
}


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, float(value)))


def calculate_overall(scores: dict) -> float:
    """Weighted rubric average converted to a 0-100 score."""
    total = sum(clamp(scores[c]) * WEIGHTS[c] for c in CRITERIA)
    return round(total * 10, 1)


def score_label(overall: float) -> str:
    if overall >= 80:
        return "Excellent"
    if overall >= 60:
        return "Good"
    if overall >= 40:
        return "Needs work"
    return "Weak"


def compute_metrics(answer_text: str, seconds: int, speech_used: bool) -> CommunicationMetrics:
    """Real measurements taken from the answer text and the timer."""
    word_count = len(answer_text.split())
    fillers = Counter(m.lower() for m in FILLER_PATTERN.findall(answer_text))
    wpm = None
    if speech_used and seconds >= 10 and word_count > 0:
        wpm = round(word_count / (seconds / 60), 1)
    return CommunicationMetrics(
        word_count=word_count,
        filler_count=sum(fillers.values()),
        filler_words=dict(fillers),
        words_per_minute=wpm,
        speech_used=speech_used,
    )


# ---------- rule-based evaluation (demo mode and AI fallback) ----------
def _keywords_for(question: dict) -> tuple[list[str], str]:
    entry = sample_data.find_bank_entry(question["text"])
    if entry:
        return entry["keywords"], entry["model_answer"]
    words = [
        w for w in re.findall(r"[a-zA-Z]{5,}", question["text"].lower()) if w not in STOPWORDS
    ]
    return list(dict.fromkeys(words))[:6], ""


def heuristic_evaluate(question: dict, answer_text: str) -> dict:
    """Keyword-coverage and length based scoring. This is an ESTIMATE, not expert judgement."""
    text = answer_text.strip()
    lower = text.lower()
    word_count = len(text.split())
    keywords, model_answer = _keywords_for(question)
    hits = [k for k in keywords if k.lower() in lower]
    missing = [k for k in keywords if k.lower() not in lower]
    coverage = len(hits) / len(keywords) if keywords else 0.0

    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    avg_sentence_len = word_count / max(len(sentences), 1)
    markers = {m for m in REASONING_MARKERS if m in lower}

    if word_count < 5:
        scores = {
            "relevance": 1.0, "correctness": 0.0, "clarity": 1.0,
            "completeness": 1.0, "problem_solving": 0.0,
        }
    else:
        clarity = 8.0 if 6 <= avg_sentence_len <= 28 else 5.0
        if word_count < 15:
            clarity = min(clarity, 4.0)
        scores = {
            "relevance": clamp(2 + 8 * min(1.0, coverage * 1.5)),
            "correctness": clamp(10 * min(1.0, coverage * 1.2)),
            "clarity": clarity,
            "completeness": clamp(5 * min(word_count / 80, 1.0) + 5 * coverage),
            "problem_solving": clamp(2 + 2 * len(markers)) if word_count >= 15 else 1.0,
        }
    scores = {k: round(v, 1) for k, v in scores.items()}

    strengths: list[str] = []
    if scores["relevance"] >= 7:
        strengths.append("Your answer stayed on topic.")
    if hits:
        strengths.append(f"You covered key ideas such as: {', '.join(hits[:3])}.")
    if scores["clarity"] >= 7:
        strengths.append("Your sentences were easy to follow.")
    if markers:
        strengths.append("You explained your reasoning (for example with 'because' or an example).")
    if not strengths:
        strengths.append("You attempted the question, which is the first step.")

    weaknesses: list[str] = []
    if missing and word_count >= 5:
        weaknesses.append("Some key ideas for this question were missing.")
    if word_count < 40:
        weaknesses.append("The answer was short. Add more detail.")
    if not markers:
        weaknesses.append("There was little visible reasoning or no example.")

    improvements = [
        "Start with a one-line definition, then explain how it works, then give a concrete example."
    ]
    if missing:
        improvements.append(f"Revise and try to mention: {', '.join(missing[:4])}.")

    return {
        "scores": scores,
        "feedback": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_concepts": missing[:5],
            "improvements": improvements,
            "stronger_answer": model_answer
            or "Structure a strong answer as: definition, how it works, a real example, then a trade-off.",
        },
    }


# ---------- validating AI output ----------
def _to_score(value: Any) -> float:
    try:
        return round(clamp(float(value)), 1)
    except (TypeError, ValueError) as exc:
        raise ValueError("AI returned a non-numeric score.") from exc


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:6]


def validate_ai_evaluation(data: dict) -> dict:
    """Check and clean the JSON returned by AI. Raises ValueError if unusable."""
    scores_in = data.get("scores")
    feedback_in = data.get("feedback")
    if not isinstance(scores_in, dict) or not isinstance(feedback_in, dict):
        raise ValueError("AI returned an unexpected evaluation format.")
    scores = {}
    for criterion in CRITERIA:
        if criterion not in scores_in:
            raise ValueError(f"AI evaluation is missing '{criterion}'.")
        scores[criterion] = _to_score(scores_in[criterion])
    feedback = {
        "strengths": _str_list(feedback_in.get("strengths")),
        "weaknesses": _str_list(feedback_in.get("weaknesses")),
        "missing_concepts": _str_list(feedback_in.get("missing_concepts")),
        "improvements": _str_list(feedback_in.get("improvements")),
        "stronger_answer": str(feedback_in.get("stronger_answer", "")).strip(),
    }
    return {"scores": scores, "feedback": feedback}


# ---------- building response objects ----------
def build_evaluation(
    raw: dict,
    question_id: int,
    metrics: CommunicationMetrics,
    source: str,
    warning: str | None = None,
) -> EvaluationOut:
    scores = {c: round(clamp(raw["scores"][c]), 1) for c in CRITERIA}
    overall = calculate_overall(scores)
    return EvaluationOut(
        question_id=question_id,
        scores=RubricScores(**scores),
        overall_score=overall,
        label=score_label(overall),
        feedback=Feedback(**raw["feedback"]),
        metrics=metrics,
        source=source,
        warning=warning,
    )


def evaluation_from_row(row: dict) -> EvaluationOut:
    """Rebuild an EvaluationOut from a stored database row."""
    return EvaluationOut(
        question_id=row["question_id"],
        scores=RubricScores(**{c: row[c] for c in CRITERIA}),
        overall_score=row["overall_score"],
        label=score_label(row["overall_score"]),
        feedback=Feedback(**json.loads(row["feedback_json"])),
        metrics=CommunicationMetrics(**json.loads(row["metrics_json"])),
        source=row["source"],
    )


def summarize_session(results: list[dict]) -> tuple[float, SessionSummary]:
    """Compute the overall score and summary from answered rows."""
    answered = [r for r in results if r["overall_score"] is not None]
    overall = round(sum(r["overall_score"] for r in answered) / len(answered), 1)

    criterion_averages = {
        c: round(sum(r[c] for r in answered) / len(answered), 1) for c in CRITERIA
    }

    by_topic: dict[str, list[float]] = {}
    for row in answered:
        by_topic.setdefault(row["topic"], []).append(row["overall_score"])
    topic_avg = {t: sum(v) / len(v) for t, v in by_topic.items()}

    summary = SessionSummary(
        answered=len(answered),
        total_questions=len(results),
        criterion_averages=criterion_averages,
        strong_topics=sorted(t for t, a in topic_avg.items() if a >= STRONG_TOPIC_THRESHOLD),
        weak_topics=sorted(t for t, a in topic_avg.items() if a < WEAK_TOPIC_THRESHOLD),
    )
    return overall, summary


def build_session_detail(session: dict, results: list[dict]) -> SessionDetail:
    items = []
    for row in results:
        answered = row["answer_text"] is not None
        question = QuestionOut(
            id=row["question_id"],
            position=row["position"],
            text=row["text"],
            topic=row["topic"],
            difficulty=row["difficulty"],
            kind=row["kind"],
            answered=answered,
        )
        items.append(
            QuestionResult(
                question=question,
                answer_text=row["answer_text"],
                time_taken_seconds=row["time_taken_seconds"],
                evaluation=evaluation_from_row(row) if answered else None,
            )
        )
    summary = None
    if session.get("summary_json"):
        summary = SessionSummary(**json.loads(session["summary_json"]))
    return SessionDetail(**session, results=items, summary=summary)