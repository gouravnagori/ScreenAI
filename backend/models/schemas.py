"""
Pydantic Schemas — Request/Response models for all API endpoints.
Provides validation, serialization, and documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─── Session Schemas ─────────────────────────────────────

class SessionStartResponse(BaseModel):
    """Response after starting a new interview session."""
    session_id: str
    role: str
    extracted_skills: list[str] = []
    extracted_experience: str = ""
    extracted_education: str = ""
    domain_exposure: list[str] = []
    first_question: Optional["QuestionOut"] = None
    total_questions: int = 0
    message: str = "Session created successfully"


class SessionStatusResponse(BaseModel):
    """Current session status and metadata."""
    session_id: str
    role: str
    status: str
    extracted_skills: list[str] = []
    total_questions: int = 0
    answered_questions: int = 0
    created_at: str = ""


# ─── Question Schemas ────────────────────────────────────

class QuestionOut(BaseModel):
    """A single interview question."""
    question_id: str
    question_text: str
    topic: str = ""
    difficulty: str = "medium"
    context_source: str = ""
    question_number: int = 1
    total_questions: int = 5


# ─── Answer Schemas ──────────────────────────────────────

class AnswerSubmitRequest(BaseModel):
    """Request to submit an answer."""
    question_id: str
    answer_text: str = Field(..., min_length=1, max_length=5000)
    time_taken_seconds: int = 0


class AnswerSubmitResponse(BaseModel):
    """Response after submitting an answer."""
    message: str = "Answer recorded"
    next_question: Optional[QuestionOut] = None
    is_complete: bool = False
    questions_remaining: int = 0


# ─── Evaluation / Summary Schemas ────────────────────────

class QuestionAnswerPair(BaseModel):
    """A single Q&A pair for the summary."""
    question: str
    answer: str
    topic: str = ""
    difficulty: str = ""
    context_source: str = ""
    score: Optional[float] = None
    feedback: Optional[str] = None
    time_taken_seconds: Optional[int] = 0


class SessionSummaryResponse(BaseModel):
    """Complete session summary with evaluation."""
    session_id: str
    role: str
    candidate_skills: list[str] = []

    # Scores
    overall_score: float = 0
    technical_depth_score: float = 0
    communication_score: float = 0
    relevance_score: float = 0

    # Qualitative
    summary: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendation: str = ""
    detailed_feedback: str = ""

    # Per-question breakdown
    qa_pairs: list[QuestionAnswerPair] = []
    topic_performance: dict[str, float] = {}

    # Metadata
    total_questions: int = 0
    total_answered: int = 0
    total_time_taken_seconds: int = 0
    created_at: str = ""


# ─── Knowledge Base Schemas ──────────────────────────────

class KnowledgeStatusResponse(BaseModel):
    """Status of the knowledge base."""
    is_ingested: bool = False
    total_chunks: int = 0
    books_loaded: list[str] = []
    message: str = ""


# Fix forward reference
SessionStartResponse.model_rebuild()
