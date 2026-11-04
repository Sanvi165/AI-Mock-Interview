"""Interview endpoints: create a session, submit answers (with adaptive follow-up), finish.

Every endpoint requires a logged-in user and only touches that user's own sessions.
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.database import repositories
from app.routes.auth import get_current_user
from app.schemas.evaluation import (
    CommunicationMetrics,
    EvaluationOut,
    Feedback,
    RubricScores,
)
from app.schemas.interview import (
    AnswerRequest,
    AnswerResponse,
    InterviewSetupRequest,
    McqResult,
    QuestionOut,
    SessionDetail,
    SessionOut,
)
from app.services import adaptive_service, ai_service, evaluation_service

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


def _get_session_or_404(session_id: int, user_id: int) -> dict:
    """404 if the session does not exist OR belongs to another user."""
    session = repositories.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return session


def _session_out(session_id: int, user_id: int, warning: Optional[str] = None) -> SessionOut:
    session = repositories.get_session(session_id, user_id)
    questions = [QuestionOut(**q) for q in repositories.get_questions(session_id)]
    return SessionOut(**session, questions=questions, warning=warning)


# ---------- multiple-choice (Aptitude) helpers ----------
def _mcq_data(question: dict) -> Optional[dict]:
    """The stored options / correct letter / explanations, or None for a normal question."""
    raw = question.get("extra_json")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    options = data.get("options")
    if not isinstance(options, list) or len(options) != 4 or data.get("answer") not in ("A", "B", "C", "D"):
        return None
    return data


def _grade_mcq(data: dict, letter: str) -> dict:
    """Compare the chosen letter with the stored correct letter."""
    options = data["options"]
    correct = data["answer"]
    return {
        "is_correct": letter == correct,
        "chosen": f"{letter}) {options[ord(letter) - 65]}",
        "correct_option": correct,
        "correct_text": f"{correct}) {options[ord(correct) - 65]}",
        "quick": str(data.get("quick", "")),
        "explanation": str(data.get("explanation", "")),
    }


def _mcq_evaluation(question_id: int, graded: dict) -> EvaluationOut:
    """A multiple-choice answer is exactly right (100) or exactly wrong (0)."""
    value = 10.0 if graded["is_correct"] else 0.0
    return EvaluationOut(
        question_id=question_id,
        scores=RubricScores(
            relevance=value,
            correctness=value,
            clarity=value,
            completeness=value,
            problem_solving=value,
        ),
        overall_score=value * 10,
        label="Correct" if graded["is_correct"] else "Wrong",
        feedback=Feedback(
            strengths=["Correct answer."] if graded["is_correct"] else [],
            weaknesses=[] if graded["is_correct"] else ["A different option was chosen."],
            stronger_answer=f"{graded['correct_text']}. {graded['explanation']}".strip(),
        ),
        metrics=CommunicationMetrics(word_count=0, filler_count=0),
        source="gemini",
    )


@router.post("", response_model=SessionOut, status_code=201)
def create_interview(
    payload: InterviewSetupRequest, user: dict = Depends(get_current_user)
) -> SessionOut:
    """Generate questions (AI or demo bank) and create a session."""
    setup = payload.model_dump()
    questions, source, warning, field = ai_service.generate_questions(setup)
    if not questions:
        # Only the Aptitude and GD rounds can end up here (they have no built-in questions).
        raise HTTPException(status_code=503, detail=warning or ai_service.NO_AI_FOR_ROUND)
    # The branch/field is worked out by the AI from the job role.
    setup["domain"] = field or setup["domain"] or setup["role"]
    session_id = repositories.create_session(user["id"], setup, questions, source)
    return _session_out(session_id, user["id"], warning)


@router.get("/{session_id}", response_model=SessionOut)
def get_interview(session_id: int, user: dict = Depends(get_current_user)) -> SessionOut:
    _get_session_or_404(session_id, user["id"])
    return _session_out(session_id, user["id"])


@router.post("/{session_id}/answers", response_model=AnswerResponse)
def submit_answer(
    session_id: int, payload: AnswerRequest, user: dict = Depends(get_current_user)
) -> AnswerResponse:
    """Evaluate one answer, save it, and decide the next question."""
    session = _get_session_or_404(session_id, user["id"])
    if session["status"] == "completed":
        raise HTTPException(status_code=409, detail="This interview is already completed.")

    question = repositories.get_question(payload.question_id)
    if question is None or question["session_id"] != session_id:
        raise HTTPException(status_code=404, detail="Question not found in this interview.")
    if repositories.has_answer(question["id"]):
        raise HTTPException(status_code=409, detail="This question was already answered.")

    mcq: Optional[McqResult] = None
    mcq_data = _mcq_data(question)
    if mcq_data:
        # Aptitude: the answer is one of A, B, C, D. Check it directly, no AI needed.
        letter = payload.answer_text.strip().upper()[:1]
        if letter not in ("A", "B", "C", "D"):
            raise HTTPException(status_code=400, detail="Please choose one of the four options.")
        graded = _grade_mcq(mcq_data, letter)
        mcq = McqResult(**graded)
        evaluation = _mcq_evaluation(question["id"], graded)
        answer_to_save = graded["chosen"]
        speech_used = False
        source = evaluation.source
    else:
        raw, source, warning = ai_service.evaluate_answer(question, payload.answer_text, session)
        metrics = evaluation_service.compute_metrics(
            payload.answer_text, payload.time_taken_seconds, payload.speech_used
        )
        evaluation = evaluation_service.build_evaluation(
            raw, question["id"], metrics, source, warning
        )
        answer_to_save = payload.answer_text
        speech_used = payload.speech_used

    repositories.save_answer(
        question_id=question["id"],
        session_id=session_id,
        answer_text=answer_to_save,
        time_taken_seconds=payload.time_taken_seconds,
        speech_used=speech_used,
        scores=evaluation.scores.model_dump(),
        overall_score=evaluation.overall_score,
        feedback=evaluation.feedback.model_dump(),
        metrics=evaluation.metrics.model_dump(),
        source=source,
    )

    # Adaptive follow-ups only make sense for job interviews. Aptitude and GD just move on.
    extras_used = repositories.count_adaptive_questions(session_id)
    if session["interview_type"] in ai_service.ROUND_TYPES:
        decision = adaptive_service.AdaptiveDecision("next", "Moving on to the next question.")
    else:
        planned_total = session["question_count"] - extras_used
        decision = adaptive_service.decide(
            evaluation.overall_score, question["kind"], extras_used, planned_total
        )

    action = decision.action
    reason = decision.reason
    if action in ("followup", "simpler"):
        generated = ai_service.generate_adaptive_question(
            question, payload.answer_text, evaluation.overall_score, action, session
        )
        next_question = repositories.insert_adaptive_question(
            session_id, question, action, generated
        )
    else:
        next_question = repositories.next_unanswered_question(session_id)
        if next_question is None:
            # Open-ended interview: when the questions run out, ask the AI for more.
            more, more_warning = ai_service.generate_more_questions(
                session, [q["text"] for q in repositories.get_questions(session_id)]
            )
            if more:
                repositories.add_planned_questions(session_id, more)
                next_question = repositories.next_unanswered_question(session_id)
                action = "next"
                reason = "Here is the next question. Finish the interview whenever you want your results."
            else:
                action = "finish"
                reason = more_warning or "Finish the interview to see your results."

    refreshed = repositories.get_session(session_id, user["id"])
    return AnswerResponse(
        evaluation=evaluation,
        mcq=mcq,
        adaptive_action=action,
        adaptive_reason=reason,
        next_question=QuestionOut(**next_question) if next_question else None,
        answered_count=refreshed["answered_count"],
        question_count=refreshed["question_count"],
    )


@router.post("/{session_id}/complete", response_model=SessionDetail)
def complete_interview(
    session_id: int, user: dict = Depends(get_current_user)
) -> SessionDetail:
    """Finish the interview (early finish is allowed) and return the full results."""
    session = _get_session_or_404(session_id, user["id"])
    results = repositories.get_results(session_id)

    if session["status"] != "completed":
        if not any(r["overall_score"] is not None for r in results):
            raise HTTPException(
                status_code=400,
                detail="Answer at least one question before finishing the interview.",
            )
        # Questions that were never answered are not kept in the results.
        repositories.delete_unanswered_questions(session_id)
        results = repositories.get_results(session_id)
        overall, summary = evaluation_service.summarize_session(results)
        repositories.complete_session(session_id, overall, summary.model_dump())
        session = repositories.get_session(session_id, user["id"])

    return evaluation_service.build_session_detail(session, results)