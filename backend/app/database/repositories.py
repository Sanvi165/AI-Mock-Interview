"""All SQL lives here. Routes and services never write SQL directly."""
import json
from datetime import datetime, timezone
from typing import Optional

from app.database.connection import get_db

SESSION_SELECT = """
SELECT s.*,
       (SELECT COUNT(*) FROM questions q WHERE q.session_id = s.id) AS question_count,
       (SELECT COUNT(*) FROM answers a WHERE a.session_id = s.id) AS answered_count
FROM sessions s
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _extra_to_json(question: dict) -> Optional[str]:
    """Multiple-choice questions carry options, the right answer and explanations."""
    extra = question.get("extra")
    return json.dumps(extra) if extra else None


def _public_question(row) -> dict:
    """A question as the website may see it: options yes, the correct answer NO."""
    data = dict(row)
    raw = data.pop("extra_json", None)
    options = None
    if raw:
        try:
            options = json.loads(raw).get("options")
        except ValueError:
            options = None
    data["options"] = options
    return data


# ---------- users and login tokens ----------
def create_user(username: str, email: str, password_hash: str) -> dict:
    """Raises sqlite3.IntegrityError if the email already exists."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, now_iso()),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def get_user_by_email(email: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def get_user_by_username(username: str) -> Optional[dict]:
    """Case-insensitive username lookup."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(username) = lower(?)", (username,)
        ).fetchone()
    return dict(row) if row else None


def save_token(token_hash: str, user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO auth_tokens (token_hash, user_id, created_at) VALUES (?, ?, ?)",
            (token_hash, user_id, now_iso()),
        )


def get_user_by_token_hash(token_hash: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            """SELECT u.*, t.created_at AS token_created_at
               FROM auth_tokens t JOIN users u ON u.id = t.user_id
               WHERE t.token_hash = ?""",
            (token_hash,),
        ).fetchone()
    return dict(row) if row else None


def delete_token(token_hash: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM auth_tokens WHERE token_hash = ?", (token_hash,))


# ---------- sessions (always scoped to one user) ----------
def create_session(
    user_id: int,
    setup: dict,
    questions: list[dict],
    ai_source: str,
    created_at: Optional[str] = None,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO sessions
               (user_id, role, domain, experience_level, interview_type,
                num_questions, status, ai_source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)""",
            (
                user_id,
                setup["role"],
                setup["domain"],
                setup["experience_level"],
                setup["interview_type"],
                len(questions),
                ai_source,
                created_at or now_iso(),
            ),
        )
        session_id = cursor.lastrowid
        for position, q in enumerate(questions, start=1):
            conn.execute(
                """INSERT INTO questions (session_id, position, text, topic, difficulty, kind, extra_json)
                   VALUES (?, ?, ?, ?, ?, 'planned', ?)""",
                (session_id, position, q["text"], q["topic"], q["difficulty"], _extra_to_json(q)),
            )
    return session_id


def get_session(session_id: int, user_id: int) -> Optional[dict]:
    """Returns None if the session does not exist OR belongs to another user."""
    with get_db() as conn:
        row = conn.execute(
            SESSION_SELECT + " WHERE s.id = ? AND s.user_id = ?", (session_id, user_id)
        ).fetchone()
    return dict(row) if row else None


def list_sessions(user_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            SESSION_SELECT + " WHERE s.user_id = ? ORDER BY s.id DESC", (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def complete_session(
    session_id: int,
    overall_score: float,
    summary: dict,
    completed_at: Optional[str] = None,
) -> None:
    with get_db() as conn:
        conn.execute(
            """UPDATE sessions
               SET status = 'completed', overall_score = ?, summary_json = ?, completed_at = ?
               WHERE id = ?""",
            (overall_score, json.dumps(summary), completed_at or now_iso(), session_id),
        )


def delete_session(session_id: int, user_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
        )
        return cursor.rowcount > 0


def delete_all_data(user_id: int) -> int:
    """Privacy control: remove every session, question and answer of one user."""
    with get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    return count


# ---------- questions (ownership is checked on the session before these are used) ----------
def get_questions(session_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT q.*,
                      EXISTS(SELECT 1 FROM answers a WHERE a.question_id = q.id) AS answered
               FROM questions q WHERE q.session_id = ? ORDER BY q.position""",
            (session_id,),
        ).fetchall()
    return [_public_question(r) for r in rows]


def get_question(question_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    return dict(row) if row else None


def has_answer(question_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT 1 FROM answers WHERE question_id = ?", (question_id,)).fetchone()
    return row is not None


def next_unanswered_question(session_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            """SELECT q.* FROM questions q
               LEFT JOIN answers a ON a.question_id = q.id
               WHERE q.session_id = ? AND a.id IS NULL
               ORDER BY q.position LIMIT 1""",
            (session_id,),
        ).fetchone()
    return _public_question(row) if row else None


def count_adaptive_questions(session_id: int) -> int:
    with get_db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM questions WHERE session_id = ? AND kind != 'planned'",
            (session_id,),
        ).fetchone()[0]


def insert_adaptive_question(session_id: int, parent: dict, kind: str, question: dict) -> dict:
    """Insert a follow-up/simpler question right after its parent question."""
    with get_db() as conn:
        parent_position = conn.execute(
            "SELECT position FROM questions WHERE id = ?", (parent["id"],)
        ).fetchone()["position"]
        conn.execute(
            "UPDATE questions SET position = position + 1 WHERE session_id = ? AND position > ?",
            (session_id, parent_position),
        )
        cursor = conn.execute(
            """INSERT INTO questions
               (session_id, position, text, topic, difficulty, kind, parent_question_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                parent_position + 1,
                question["text"],
                question["topic"],
                question["difficulty"],
                kind,
                parent["id"],
            ),
        )
        row = conn.execute("SELECT * FROM questions WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _public_question(row)


# ---------- add / remove questions (open-ended interviews) ----------
def add_planned_questions(session_id: int, questions: list[dict]) -> None:
    """Append a new batch of questions at the end of an open-ended interview."""
    with get_db() as conn:
        last = conn.execute(
            "SELECT COALESCE(MAX(position), 0) FROM questions WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
        for offset, q in enumerate(questions, start=1):
            conn.execute(
                """INSERT INTO questions (session_id, position, text, topic, difficulty, kind, extra_json)
                   VALUES (?, ?, ?, ?, ?, 'planned', ?)""",
                (session_id, last + offset, q["text"], q["topic"], q["difficulty"], _extra_to_json(q)),
            )


def delete_unanswered_questions(session_id: int) -> None:
    """When the interview is finished, drop questions that were never answered."""
    with get_db() as conn:
        conn.execute(
            """DELETE FROM questions
               WHERE session_id = ?
                 AND id NOT IN (SELECT question_id FROM answers WHERE session_id = ?)""",
            (session_id, session_id),
        )


# ---------- answers ----------
def save_answer(
    *,
    question_id: int,
    session_id: int,
    answer_text: str,
    time_taken_seconds: int,
    speech_used: bool,
    scores: dict,
    overall_score: float,
    feedback: dict,
    metrics: dict,
    source: str,
    created_at: Optional[str] = None,
) -> None:
    with get_db() as conn:
        conn.execute(
            """INSERT INTO answers
               (question_id, session_id, answer_text, time_taken_seconds, speech_used,
                relevance, correctness, clarity, completeness, problem_solving,
                overall_score, feedback_json, metrics_json, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                question_id,
                session_id,
                answer_text,
                time_taken_seconds,
                1 if speech_used else 0,
                scores["relevance"],
                scores["correctness"],
                scores["clarity"],
                scores["completeness"],
                scores["problem_solving"],
                overall_score,
                json.dumps(feedback),
                json.dumps(metrics),
                source,
                created_at or now_iso(),
            ),
        )


def get_results(session_id: int) -> list[dict]:
    """Every question of a session, joined with its answer (answer columns are NULL if unanswered)."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT q.id AS question_id, q.position, q.text, q.topic, q.difficulty, q.kind,
                      a.answer_text, a.time_taken_seconds, a.speech_used,
                      a.relevance, a.correctness, a.clarity, a.completeness, a.problem_solving,
                      a.overall_score, a.feedback_json, a.metrics_json, a.source
               FROM questions q
               LEFT JOIN answers a ON a.question_id = q.id
               WHERE q.session_id = ?
               ORDER BY q.position""",
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- analytics (per user) ----------
def topic_stats(user_id: int) -> list[dict]:
    """Average score per topic across one user's answers, weakest first."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT q.topic AS topic, AVG(a.overall_score) AS average_score, COUNT(*) AS attempts
               FROM answers a
               JOIN questions q ON q.id = a.question_id
               JOIN sessions s ON s.id = q.session_id
               WHERE s.user_id = ?
               GROUP BY q.topic ORDER BY average_score ASC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def session_points(user_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, created_at, role, overall_score FROM sessions
               WHERE user_id = ? AND status = 'completed' AND overall_score IS NOT NULL
               ORDER BY id ASC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def feedback_for_topic(topic: str, user_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT a.feedback_json, a.overall_score
               FROM answers a
               JOIN questions q ON q.id = a.question_id
               JOIN sessions s ON s.id = q.session_id
               WHERE q.topic = ? AND s.user_id = ?
               ORDER BY a.overall_score ASC LIMIT 10""",
            (topic, user_id),
        ).fetchall()
    return [dict(r) for r in rows]


def asked_question_texts(user_id: int) -> set[str]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DISTINCT q.text FROM questions q
               JOIN sessions s ON s.id = q.session_id
               WHERE s.user_id = ?""",
            (user_id,),
        ).fetchall()
    return {r["text"] for r in rows}