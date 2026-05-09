"""
Knowledge Router — Handles knowledge base management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import KnowledgeStatusResponse
from services import rag_service

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])


@router.get("/status", response_model=KnowledgeStatusResponse)
async def get_knowledge_status():
    """Check the current status of the knowledge base."""
    status = rag_service.get_ingestion_status()
    return KnowledgeStatusResponse(
        is_ingested=status["is_ingested"],
        total_chunks=status["total_chunks"],
        books_loaded=status["books_loaded"],
        message="Knowledge base is ready" if status["is_ingested"] else "Knowledge base not yet ingested",
    )


@router.post("/ingest", response_model=KnowledgeStatusResponse)
async def ingest_knowledge_base(background_tasks: BackgroundTasks):
    """
    Trigger knowledge base ingestion.
    Processes all PDF files in the knowledge_base/books/ directory.
    """
    # Run ingestion (this can take a while for large PDFs)
    result = rag_service.ingest_knowledge_base()

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    status = rag_service.get_ingestion_status()
    return KnowledgeStatusResponse(
        is_ingested=status["is_ingested"],
        total_chunks=status["total_chunks"],
        books_loaded=status["books_loaded"],
        message=result["message"],
    )
