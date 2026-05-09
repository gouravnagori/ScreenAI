"""
Configuration — Environment variables and application settings.
Uses pydantic-settings for validation and type safety.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ─── API Keys ────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ─── Paths ───────────────────────────────────────────
    DATABASE_PATH: str = str(BASE_DIR / "data" / "screening.db")
    CHROMA_DB_PATH: str = str(BASE_DIR / "knowledge_base" / "chroma_db")
    KNOWLEDGE_BASE_PATH: str = str(BASE_DIR / "knowledge_base" / "books")
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")

    # ─── RAG Configuration ───────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500        # tokens per chunk
    CHUNK_OVERLAP: int = 50      # token overlap between chunks
    RAG_TOP_K: int = 5           # number of chunks to retrieve
    RAG_SCORE_THRESHOLD: float = 0.4  # minimum similarity score

    # ─── LLM Configuration ───────────────────────────────
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    # ─── Interview Configuration ─────────────────────────
    QUESTIONS_PER_SESSION: int = 7
    ENABLE_ADAPTIVE_QUESTIONS: bool = True

    # ─── Server ──────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]  # Allow Vercel frontend to connect

    class Config:
        env_file = str(BASE_DIR.parent / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure required directories exist
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
os.makedirs(settings.KNOWLEDGE_BASE_PATH, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
