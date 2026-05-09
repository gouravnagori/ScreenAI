"""
Database Layer — SQLite schema and connection management.
Handles all persistence for sessions, questions, answers, and evaluations.
"""

import json
import sqlite3
import os
from datetime import datetime
from config import settings


def get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection with row factory enabled."""
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                resume_text TEXT,
                resume_filename TEXT,
                extracted_skills TEXT,  -- JSON array
                extracted_experience TEXT,
                extracted_education TEXT,
                domain_exposure TEXT,   -- JSON array
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                topic TEXT,
                difficulty TEXT,
                context_source TEXT,    -- which book/section the context came from
                rag_context TEXT,       -- the actual retrieved context
                question_order INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS answers (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                overall_score REAL,
                technical_depth_score REAL,
                communication_score REAL,
                relevance_score REAL,
                scores_json TEXT,       -- detailed per-question scores
                summary TEXT,
                strengths TEXT,         -- JSON array
                weaknesses TEXT,        -- JSON array
                recommendation TEXT,
                detailed_feedback TEXT,
                topic_performance TEXT, -- JSON object {topic: score}
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)
        conn.commit()
    finally:
        conn.close()


# ─── Session Operations ──────────────────────────────────

def create_session(session_id: str, role: str, resume_text: str,
                   resume_filename: str, extracted_skills: list,
                   extracted_experience: str, extracted_education: str,
                   domain_exposure: list) -> dict:
    """Create a new interview session."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO sessions
            (id, role, resume_text, resume_filename, extracted_skills,
             extracted_experience, extracted_education, domain_exposure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, role, resume_text, resume_filename,
            json.dumps(extracted_skills), extracted_experience,
            extracted_education, json.dumps(domain_exposure)
        ))
        conn.commit()
        return get_session(session_id)
    finally:
        conn.close()


def get_session(session_id: str) -> dict | None:
    """Get session by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row:
            data = dict(row)
            data["extracted_skills"] = json.loads(data["extracted_skills"] or "[]")
            data["domain_exposure"] = json.loads(data["domain_exposure"] or "[]")
            return data
        return None
    finally:
        conn.close()


def update_session_status(session_id: str, status: str):
    """Update session status."""
    conn = get_connection()
    try:
        updates = {"status": status}
        if status == "completed":
            conn.execute(
                "UPDATE sessions SET status = ?, completed_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), session_id)
            )
        else:
            conn.execute(
                "UPDATE sessions SET status = ? WHERE id = ?",
                (status, session_id)
            )
        conn.commit()
    finally:
        conn.close()


# ─── Question Operations ─────────────────────────────────

def save_questions(questions: list[dict]):
    """Save a batch of questions."""
    conn = get_connection()
    try:
        conn.executemany("""
            INSERT INTO questions
            (id, session_id, question_text, topic, difficulty,
             context_source, rag_context, question_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (q["id"], q["session_id"], q["question_text"], q.get("topic", ""),
             q.get("difficulty", "medium"), q.get("context_source", ""),
             q.get("rag_context", ""), q.get("question_order", 0))
            for q in questions
        ])
        conn.commit()
    finally:
        conn.close()


def get_session_questions(session_id: str) -> list[dict]:
    """Get all questions for a session, ordered."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT q.*, a.answer_text, a.submitted_at as answered_at
            FROM questions q
            LEFT JOIN answers a ON q.id = a.question_id
            WHERE q.session_id = ?
            ORDER BY q.question_order
        """, (session_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_next_unanswered_question(session_id: str) -> dict | None:
    """Get the next question that hasn't been answered yet."""
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT q.*
            FROM questions q
            LEFT JOIN answers a ON q.id = a.question_id
            WHERE q.session_id = ? AND a.id IS NULL
            ORDER BY q.question_order
            LIMIT 1
        """, (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ─── Answer Operations ───────────────────────────────────

def save_answer(answer_id: str, question_id: str, session_id: str,
                answer_text: str) -> dict:
    """Save a candidate's answer."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO answers (id, question_id, session_id, answer_text)
            VALUES (?, ?, ?, ?)
        """, (answer_id, question_id, session_id, answer_text))
        conn.commit()
        row = conn.execute(
            "SELECT * FROM answers WHERE id = ?", (answer_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_session_answers(session_id: str) -> list[dict]:
    """Get all answers for a session with their questions."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT q.question_text, q.topic, q.difficulty, q.context_source,
                   q.rag_context, a.answer_text, a.submitted_at
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.session_id = ?
            ORDER BY q.question_order
        """, (session_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ─── Evaluation Operations ───────────────────────────────

def save_evaluation(eval_id: str, session_id: str, evaluation: dict):
    """Save the final evaluation for a session."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO evaluations
            (id, session_id, overall_score, technical_depth_score,
             communication_score, relevance_score, scores_json,
             summary, strengths, weaknesses, recommendation,
             detailed_feedback, topic_performance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            eval_id, session_id,
            evaluation.get("overall_score", 0),
            evaluation.get("technical_depth_score", 0),
            evaluation.get("communication_score", 0),
            evaluation.get("relevance_score", 0),
            json.dumps(evaluation.get("per_question_scores", [])),
            evaluation.get("summary", ""),
            json.dumps(evaluation.get("strengths", [])),
            json.dumps(evaluation.get("weaknesses", [])),
            evaluation.get("recommendation", ""),
            evaluation.get("detailed_feedback", ""),
            json.dumps(evaluation.get("topic_performance", {}))
        ))
        conn.commit()
    finally:
        conn.close()


def get_evaluation(session_id: str) -> dict | None:
    """Get evaluation for a session."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM evaluations WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row:
            data = dict(row)
            data["scores_json"] = json.loads(data["scores_json"] or "[]")
            data["strengths"] = json.loads(data["strengths"] or "[]")
            data["weaknesses"] = json.loads(data["weaknesses"] or "[]")
            data["topic_performance"] = json.loads(data["topic_performance"] or "{}")
            return data
        return None
    finally:
        conn.close()
