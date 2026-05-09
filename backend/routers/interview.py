"""
Interview Router — Handles the interview question/answer lifecycle.
"""

from fastapi import APIRouter, HTTPException
from models import database
from models.schemas import (
    QuestionOut, AnswerSubmitRequest, AnswerSubmitResponse,
    SessionSummaryResponse, QuestionAnswerPair,
)
from services import question_service, evaluation_service

router = APIRouter(prefix="/api/interview", tags=["Interview"])


@router.get("/{session_id}/question", response_model=QuestionOut)
async def get_next_question(session_id: str):
    """Get the next unanswered question for the session."""
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    question = question_service.get_next_question(session_id)
    if not question:
        raise HTTPException(
            status_code=404,
            detail="No more questions. Submit the interview to get your evaluation."
        )

    all_questions = database.get_session_questions(session_id)
    total = len(all_questions)
    # Calculate question number (how many have been answered + 1)
    answered = sum(1 for q in all_questions if q.get("answer_text"))

    return QuestionOut(
        question_id=question["id"],
        question_text=question["question_text"],
        topic=question.get("topic", ""),
        difficulty=question.get("difficulty", "medium"),
        context_source=question.get("context_source", ""),
        question_number=answered + 1,
        total_questions=total,
    )


@router.post("/{session_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(session_id: str, request: AnswerSubmitRequest):
    """Submit an answer to an interview question."""
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    # Submit answer (includes adaptive follow-up logic)
    result = question_service.submit_answer(
        session_id=session_id,
        question_id=request.question_id,
        answer_text=request.answer_text,
    )

    # Build next question response
    next_question = None
    if not result["is_complete"]:
        next_q = question_service.get_next_question(session_id)
        if next_q:
            all_questions = database.get_session_questions(session_id)
            total = len(all_questions)
            answered = sum(1 for q in all_questions if q.get("answer_text"))
            next_question = QuestionOut(
                question_id=next_q["id"],
                question_text=next_q["question_text"],
                topic=next_q.get("topic", ""),
                difficulty=next_q.get("difficulty", "medium"),
                context_source=next_q.get("context_source", ""),
                question_number=answered + 1,
                total_questions=total,
            )

    return AnswerSubmitResponse(
        message="Answer recorded successfully",
        next_question=next_question,
        is_complete=result["is_complete"],
        questions_remaining=result["questions_remaining"],
    )


@router.post("/{session_id}/complete", response_model=SessionSummaryResponse)
async def complete_interview(session_id: str):
    """
    Complete the interview and generate evaluation.
    Triggers the LLM-based evaluation pipeline.
    """
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate evaluation
    try:
        evaluation_service.generate_session_evaluation(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return full summary
    summary = evaluation_service.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary")

    return SessionSummaryResponse(
        session_id=summary["session_id"],
        role=summary["role"],
        candidate_skills=summary.get("candidate_skills", []),
        overall_score=summary.get("overall_score", 0),
        technical_depth_score=summary.get("technical_depth_score", 0),
        communication_score=summary.get("communication_score", 0),
        relevance_score=summary.get("relevance_score", 0),
        summary=summary.get("summary", ""),
        strengths=summary.get("strengths", []),
        weaknesses=summary.get("weaknesses", []),
        recommendation=summary.get("recommendation", ""),
        detailed_feedback=summary.get("detailed_feedback", ""),
        qa_pairs=[
            QuestionAnswerPair(**qa) for qa in summary.get("qa_pairs", [])
        ],
        topic_performance=summary.get("topic_performance", {}),
        total_questions=summary.get("total_questions", 0),
        total_answered=summary.get("total_answered", 0),
        created_at=summary.get("created_at", ""),
    )


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_interview_summary(session_id: str):
    """Get the evaluation summary for a completed interview."""
    summary = evaluation_service.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found or not yet evaluated")

    return SessionSummaryResponse(
        session_id=summary["session_id"],
        role=summary["role"],
        candidate_skills=summary.get("candidate_skills", []),
        overall_score=summary.get("overall_score", 0),
        technical_depth_score=summary.get("technical_depth_score", 0),
        communication_score=summary.get("communication_score", 0),
        relevance_score=summary.get("relevance_score", 0),
        summary=summary.get("summary", ""),
        strengths=summary.get("strengths", []),
        weaknesses=summary.get("weaknesses", []),
        recommendation=summary.get("recommendation", ""),
        detailed_feedback=summary.get("detailed_feedback", ""),
        qa_pairs=[
            QuestionAnswerPair(**qa) for qa in summary.get("qa_pairs", [])
        ],
        topic_performance=summary.get("topic_performance", {}),
        total_questions=summary.get("total_questions", 0),
        total_answered=summary.get("total_answered", 0),
        created_at=summary.get("created_at", ""),
    )
