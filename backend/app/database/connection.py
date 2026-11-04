"""SQLite connection helper and table creation.

SQLite is built into Python, so no database server or password is needed.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "interview.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    domain TEXT NOT NULL,
    experience_level TEXT NOT NULL,
    interview_type TEXT NOT NULL,
    num_questions INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    ai_source TEXT NOT NULL DEFAULT 'demo',
    overall_score REAL,
    summary_json TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    text TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'planned',
    parent_question_id INTEGER,
    extra_json TEXT
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL UNIQUE REFERENCES questions(id) ON DELETE CASCADE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    time_taken_seconds INTEGER NOT NULL DEFAULT 0,
    speech_used INTEGER NOT NULL DEFAULT 0,
    relevance REAL,
    correctness REAL,
    clarity REAL,
    completeness REAL,
    problem_solving REAL,
    overall_score REAL NOT NULL,
    feedback_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(lower(username));
CREATE INDEX IF NOT EXISTS idx_questions_session ON questions(session_id);
CREATE INDEX IF NOT EXISTS idx_answers_session ON answers(session_id);
"""

# Old versions of this project had users(id, name, created_at) with no login columns.
OLD_USERS_TO_NEW = """
PRAGMA foreign_keys = OFF;
BEGIN;
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
-- The one old default user becomes the disabled "guest" account (nobody can log in as it).
INSERT INTO users_new (id, username, email, password_hash, created_at)
    SELECT id, 'guest', 'guest@local.invalid', '!disabled', created_at
    FROM users ORDER BY id LIMIT 1;
DROP TABLE users;
ALTER TABLE users_new RENAME TO users;
COMMIT;
PRAGMA foreign_keys = ON;
"""


def db_path() -> Path:
    custom = os.getenv("DATABASE_PATH", "").strip()
    return Path(custom) if custom else DEFAULT_DB_PATH


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _upgrade_old_users_table(conn: sqlite3.Connection) -> None:
    """Upgrade a database created before the Sign up / Log in feature existed."""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
    if columns and "username" not in columns:
        conn.executescript(OLD_USERS_TO_NEW)


def _add_missing_question_columns(conn: sqlite3.Connection) -> None:
    """Older database files have no extra_json column (it stores multiple-choice options)."""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(questions)")]
    if columns and "extra_json" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN extra_json TEXT")


def init_db() -> None:
    """Create tables (if missing). Upgrades an old database file automatically."""
    db_path().parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        _upgrade_old_users_table(conn)
        _add_missing_question_columns(conn)
        conn.executescript(SCHEMA)