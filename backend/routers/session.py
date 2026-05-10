"""
Session Router — Handles session creation and status endpoints.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models import database
from models.schemas import SessionStartResponse, SessionStatusResponse, QuestionOut
from services import resume_parser, question_service

router = APIRouter(prefix="/api/session", tags=["Session"])
    
@router.get("/", response_model=list[dict])
async def get_all_sessions():
    """Get all sessions for HR dashboard."""
    return database.get_all_sessions_hr()

@router.post("/start", response_model=SessionStartResponse)
async def start_session(
    resume: UploadFile = File(...),
    role: str = Form(...),
):
    """
    Start a new interview session.
    
    Flow:
    1. Parse uploaded resume
    2. Extract skills, experience, education, domains
    3. Generate interview questions (RAG pipeline)
    4. Return session info + first question
    """
    # Validate role
    valid_roles = ["AI/ML Engineer", "Data Scientist", "Backend Engineer", "Full-Stack Developer"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    # Validate file
    if not resume.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    allowed_extensions = [".pdf", ".txt", ".text"]
    file_ext = "." + resume.filename.rsplit(".", 1)[-1].lower() if "." in resume.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File must be PDF or text format")

    # Read file
    file_bytes = await resume.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB")

    # Parse resume
    resume_data = resume_parser.parse_resume(file_bytes, resume.filename)

    if not resume_data["text"].strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the uploaded file. Please ensure the PDF contains selectable text."
        )

    # Create session
    session_id = str(uuid.uuid4())
    database.create_session(
        session_id=session_id,
        role=role,
        resume_text=resume_data["text"],
        resume_filename=resume.filename,
        extracted_skills=resume_data["skills"],
        extracted_experience=resume_data["experience"],
        extracted_education=resume_data["education"],
        domain_exposure=resume_data["domains"],
    )

    # Generate questions using RAG pipeline
    questions = question_service.generate_interview_questions(
        session_id=session_id,
        skills=resume_data["skills"],
        role=role,
        experience=resume_data["experience"],
        domains=resume_data["domains"],
    )

    # Get first question
    first_question = None
    if questions:
        q = questions[0]
        first_question = QuestionOut(
            question_id=q["id"],
            question_text=q["question_text"],
            topic=q.get("topic", ""),
            difficulty=q.get("difficulty", "medium"),
            context_source=q.get("context_source", ""),
            question_number=1,
            total_questions=len(questions),
        )

    return SessionStartResponse(
        session_id=session_id,
        role=role,
        extracted_skills=resume_data["skills"],
        extracted_experience=resume_data["experience"],
        extracted_education=resume_data["education"],
        domain_exposure=resume_data["domains"],
        first_question=first_question,
        total_questions=len(questions),
        message="Interview session created. Your questions are ready!",
    )


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """Get current session status and metadata."""
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = database.get_session_questions(session_id)
    answered = sum(1 for q in questions if q.get("answer_text"))

    return SessionStatusResponse(
        session_id=session_id,
        role=session["role"],
        status=session["status"],
        extracted_skills=session.get("extracted_skills", []),
        total_questions=len(questions),
        answered_questions=answered,
        created_at=session.get("created_at", ""),
    )
