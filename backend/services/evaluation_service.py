"""
Evaluation Service — Generates final interview evaluation and structured summary.
"""

import uuid
from services import llm_service
from models import database


def generate_session_evaluation(session_id: str) -> dict:
    """
    Generate a comprehensive evaluation for a completed interview session.
    
    Pipeline:
    1. Fetch session data (role, skills, experience)
    2. Fetch all Q&A pairs
    3. Send to LLM for evaluation
    4. Store evaluation in database
    5. Mark session as completed
    
    Returns:
        Full evaluation dict.
    """
    session = database.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    qa_pairs = database.get_session_answers(session_id)
    if not qa_pairs:
        raise ValueError(f"No answers found for session {session_id}")

    # Generate evaluation via LLM
    evaluation = llm_service.generate_evaluation(
        qa_pairs=qa_pairs,
        role=session["role"],
        skills=session.get("extracted_skills", []),
        experience=session.get("extracted_experience", "Not specified"),
    )

    # Store evaluation
    eval_id = str(uuid.uuid4())
    database.save_evaluation(eval_id, session_id, evaluation)

    # Mark session as completed
    database.update_session_status(session_id, "completed")

    return evaluation


def get_session_summary(session_id: str) -> dict:
    """
    Build a complete session summary for the report view.
    
    Returns:
        Comprehensive summary dict with all session data.
    """
    session = database.get_session(session_id)
    if not session:
        return None

    evaluation = database.get_evaluation(session_id)
    qa_data = database.get_session_questions(session_id)

    # Build Q&A pairs
    qa_pairs = []
    for q in qa_data:
        pair = {
            "question": q["question_text"],
            "answer": q.get("answer_text", "Not answered"),
            "topic": q.get("topic", ""),
            "difficulty": q.get("difficulty", ""),
            "context_source": q.get("context_source", ""),
        }

        # Add per-question score if available
        if evaluation and evaluation.get("scores_json"):
            for score_item in evaluation["scores_json"]:
                if isinstance(score_item, dict) and score_item.get("question_number") == q.get("question_order"):
                    pair["score"] = score_item.get("score")
                    pair["feedback"] = score_item.get("feedback")
                    break

        qa_pairs.append(pair)

    total_answered = sum(1 for q in qa_data if q.get("answer_text"))

    summary = {
        "session_id": session_id,
        "role": session["role"],
        "candidate_skills": session.get("extracted_skills", []),
        "total_questions": len(qa_data),
        "total_answered": total_answered,
        "qa_pairs": qa_pairs,
        "created_at": session.get("created_at", ""),
    }

    if evaluation:
        summary.update({
            "overall_score": evaluation.get("overall_score", 0),
            "technical_depth_score": evaluation.get("technical_depth_score", 0),
            "communication_score": evaluation.get("communication_score", 0),
            "relevance_score": evaluation.get("relevance_score", 0),
            "summary": evaluation.get("summary", ""),
            "strengths": evaluation.get("strengths", []),
            "weaknesses": evaluation.get("weaknesses", []),
            "recommendation": evaluation.get("recommendation", ""),
            "detailed_feedback": evaluation.get("detailed_feedback", ""),
            "topic_performance": evaluation.get("topic_performance", {}),
        })

    return summary
