"""
Question Service — Orchestrates the full question generation pipeline.
Connects resume parsing → RAG retrieval → LLM question generation.
Manages the interview question lifecycle.
"""

import uuid
from services import rag_service, llm_service
from models import database
from config import settings


def generate_interview_questions(
    session_id: str,
    skills: list[str],
    role: str,
    experience: str,
    domains: list[str] = None,
) -> list[dict]:
    """
    Full pipeline: construct queries → retrieve context → generate questions → store.
    
    This is the core orchestration function that ties the RAG pipeline together:
    1. Build meaningful queries from candidate profile
    2. Retrieve relevant knowledge base chunks
    3. Generate context-grounded questions via LLM
    4. Store questions in database with full traceability
    
    Args:
        session_id: Active session ID.
        skills: Extracted skills from resume.
        role: Target role.
        experience: Experience level.
        domains: Domain exposures from resume.
        
    Returns:
        List of generated question dicts.
    """
    # Step 1: Construct RAG queries from candidate profile
    queries = rag_service.build_rag_queries(skills, role, domains)

    # Step 2: Retrieve relevant context from knowledge base
    all_contexts = []
    seen_texts = set()

    for query in queries:
        chunks = rag_service.retrieve_context(
            query=query,
            role=role,
            top_k=3,  # 3 per query to get diverse results
        )
        for chunk in chunks:
            # Deduplicate by content hash
            text_hash = hash(chunk["text"][:200])
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                all_contexts.append(chunk)

    # Sort by similarity and take top results
    all_contexts.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    top_contexts = all_contexts[:10]

    # Step 3: Generate questions using LLM + retrieved context
    num_questions = settings.QUESTIONS_PER_SESSION
    questions = llm_service.generate_questions(
        skills=skills,
        role=role,
        experience=experience,
        rag_contexts=top_contexts,
        num_questions=num_questions,
    )

    # Step 4: Store questions in database with context traceability
    db_questions = []
    for i, q in enumerate(questions):
        question_id = str(uuid.uuid4())
        # Find the context that was most relevant to this question's topic
        relevant_context = _find_relevant_context(q.get("topic", ""), top_contexts)

        db_question = {
            "id": question_id,
            "session_id": session_id,
            "question_text": q["question_text"],
            "topic": q.get("topic", "General"),
            "difficulty": q.get("difficulty", "medium"),
            "context_source": q.get("context_source", ""),
            "rag_context": relevant_context.get("text", "")[:500] if relevant_context else "",
            "question_order": i + 1,
        }
        db_questions.append(db_question)

    database.save_questions(db_questions)

    return db_questions


def get_next_question(session_id: str) -> dict | None:
    """Get the next unanswered question for the session."""
    return database.get_next_unanswered_question(session_id)


def submit_answer(
    session_id: str,
    question_id: str,
    answer_text: str,
) -> dict:
    """
    Submit an answer and optionally generate an adaptive follow-up.
    
    Returns:
        Dict with answer status and optional follow-up question.
    """
    answer_id = str(uuid.uuid4())
    database.save_answer(answer_id, question_id, session_id, answer_text)

    # Check for adaptive follow-up if enabled
    follow_up = None
    if settings.ENABLE_ADAPTIVE_QUESTIONS:
        questions = database.get_session_questions(session_id)
        # Find the current question
        current_q = next((q for q in questions if q["id"] == question_id), None)

        if current_q and current_q.get("rag_context"):
            # Try to generate adaptive follow-up
            follow_up_data = llm_service.generate_adaptive_followup(
                previous_question=current_q["question_text"],
                answer=answer_text,
                rag_contexts=[{"text": current_q["rag_context"], "source": current_q.get("context_source", "")}],
                role=database.get_session(session_id).get("role", ""),
            )

            if follow_up_data and isinstance(follow_up_data, dict):
                follow_up_id = str(uuid.uuid4())
                follow_up = {
                    "id": follow_up_id,
                    "session_id": session_id,
                    "question_text": follow_up_data["question_text"],
                    "topic": follow_up_data.get("topic", current_q.get("topic", "")),
                    "difficulty": follow_up_data.get("difficulty", "medium"),
                    "context_source": "Adaptive follow-up",
                    "rag_context": current_q.get("rag_context", ""),
                    "question_order": len(questions) + 1,
                }
                database.save_questions([follow_up])

    # Get remaining questions count
    all_questions = database.get_session_questions(session_id)
    unanswered = [q for q in all_questions if not q.get("answer_text")]

    return {
        "answer_saved": True,
        "follow_up": follow_up,
        "questions_remaining": len(unanswered),
        "is_complete": len(unanswered) == 0,
    }


def _find_relevant_context(topic: str, contexts: list[dict]) -> dict | None:
    """Find the most relevant context chunk for a given topic."""
    if not contexts or not topic:
        return contexts[0] if contexts else None

    topic_lower = topic.lower()
    for ctx in contexts:
        text_lower = ctx.get("text", "").lower()
        # Simple keyword overlap check
        topic_words = set(topic_lower.split())
        text_words = set(text_lower.split())
        overlap = len(topic_words & text_words)
        if overlap >= 2:
            return ctx

    return contexts[0] if contexts else None
