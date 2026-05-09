"""
AI-Powered Candidate Screening System — FastAPI Backend
Main application entry point.

Architecture:
- /api/session/* — Session management (create, status)
- /api/interview/* — Interview lifecycle (questions, answers, complete)
- /api/knowledge/* — Knowledge base management (ingest, status)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import init_database
from routers import session, interview, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — runs on startup and shutdown."""
    # Startup
    print("[*] Initializing database...")
    init_database()
    print("[OK] Database ready")

    # Auto-ingest knowledge base if books are available
    from services.rag_service import get_ingestion_status, ingest_knowledge_base
    status = get_ingestion_status()
    if not status["is_ingested"]:
        print("[*] Knowledge base not found. Attempting auto-ingestion...")
        result = ingest_knowledge_base()
        if result.get("success"):
            print(f"[OK] {result['message']}")
        else:
            print(f"[WARN] {result.get('message', 'No books found')} - Add PDFs to backend/knowledge_base/books/")
    else:
        print(f"[OK] Knowledge base ready ({status['total_chunks']} chunks from {len(status['books_loaded'])} books)")

    print("[OK] Server ready!")
    yield
    # Shutdown
    print("Shutting down...")


# ─── Create FastAPI App ──────────────────────────────────
app = FastAPI(
    title="AI Candidate Screening System",
    description="AI-powered role-based candidate screening with RAG pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Mount Routers ───────────────────────────────────────
app.include_router(session.router)
app.include_router(interview.router)
app.include_router(knowledge.router)


# ─── Health Check ────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from services.rag_service import get_ingestion_status
    kb_status = get_ingestion_status()
    return {
        "status": "healthy",
        "knowledge_base": {
            "ingested": kb_status["is_ingested"],
            "chunks": kb_status["total_chunks"],
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
