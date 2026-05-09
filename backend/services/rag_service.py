"""
RAG Service — Retrieval-Augmented Generation pipeline.
Handles knowledge base ingestion, embedding, storage, and retrieval.

Design decisions:
- ChromaDB: Persistent, file-based vector store — no external server needed
- all-MiniLM-L6-v2: Fast CPU-friendly embeddings with good semantic quality
- 500-token chunks with 50-token overlap: Balances context preservation with retrieval precision
- Metadata tagging: Each chunk carries book title, chapter info, and role tags for filtered retrieval
"""

import os
import re
import hashlib
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings

# Global clients (lazy-initialized)
_chroma_client = None
_collection = None
_embedding_fn = None


# ─── Role-to-Book Mapping ───────────────────────────────
ROLE_BOOK_TAGS = {
    "AI/ML Engineer": ["ml_mitchell", "ml_burkov", "ml_beginners"],
    "Data Scientist": ["ml_python", "ml_algorithms", "ml_burkov"],
    "Backend Engineer": ["ml_beginners", "ml_burkov"],
    "Full-Stack Developer": ["ml_beginners", "ml_burkov"],
}

BOOK_IDENTIFIERS = {
    "mitchell": "ml_mitchell",
    "tom mitchell": "ml_mitchell",
    "machine learning tom": "ml_mitchell",
    "ml_fundamentals": "ml_mitchell",
    "fundamentals_mitchell": "ml_mitchell",
    "burkov": "ml_burkov",
    "hundred-page": "ml_burkov",
    "hundred page": "ml_burkov",
    "deep_learning_burkov": "ml_burkov",
    "deep_learning": "ml_burkov",
    "beginners": "ml_beginners",
    "absolute beginners": "ml_beginners",
    "introduction to machine learning with python": "ml_python",
    "mueller": "ml_python",
    "brownlee": "ml_algorithms",
    "master machine learning": "ml_algorithms",
    "applied_ml": "ml_algorithms",
    "applied_ml_algorithms": "ml_algorithms",
    "bishop": "ml_bishop",
    "pattern recognition": "ml_bishop",
    "artificial intelligence": "ml_ai_dl",
}


def _get_embedding_function():
    """Lazy-load the sentence-transformers embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils import embedding_functions
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
    return _embedding_fn


def _get_collection():
    """Get or create the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        _collection = _chroma_client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=_get_embedding_function(),
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def get_ingestion_status() -> dict:
    """Check the current state of the knowledge base."""
    try:
        collection = _get_collection()
        count = collection.count()

        # Get unique book tags
        books = set()
        if count > 0:
            # Sample some metadata
            results = collection.get(limit=min(count, 100), include=["metadatas"])
            for meta in results["metadatas"]:
                if meta and "book_tag" in meta:
                    books.add(meta["book_tag"])

        return {
            "is_ingested": count > 0,
            "total_chunks": count,
            "books_loaded": sorted(list(books)),
        }
    except Exception as e:
        return {
            "is_ingested": False,
            "total_chunks": 0,
            "books_loaded": [],
            "error": str(e),
        }


def ingest_knowledge_base() -> dict:
    """
    Ingest all books (PDF and TXT) from the knowledge base directory.
    
    Process:
    1. Scan for PDF/TXT files in the knowledge_base/books/ directory
    2. Extract text from each file
    3. Chunk the text into ~500-token segments with 50-token overlap
    4. Tag chunks with book metadata (title, book_tag, page range)
    5. Generate embeddings and store in ChromaDB
    
    Returns:
        Status dict with ingestion results.
    """
    books_dir = Path(settings.KNOWLEDGE_BASE_PATH)
    book_files = list(books_dir.glob("*.pdf")) + list(books_dir.glob("*.txt"))

    if not book_files:
        return {
            "success": False,
            "message": f"No book files found in {books_dir}. Please add textbook PDFs or TXT files.",
            "books_processed": 0,
            "total_chunks": 0,
        }

    collection = _get_collection()
    total_chunks = 0
    books_processed = []

    for book_path in book_files:
        try:
            print(f"Ingesting: {book_path.name}")
            book_tag = _identify_book(book_path.name)
            text = _extract_file_text(book_path)

            if not text.strip():
                print(f"  [WARN] No text extracted from {book_path.name}")
                continue

            chunks = _chunk_text(text, book_path.name)

            if not chunks:
                continue

            # Batch insert into ChromaDB
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                ids = [c["id"] for c in batch]
                documents = [c["text"] for c in batch]
                metadatas = [c["metadata"] for c in batch]

                # Skip chunks that already exist
                try:
                    existing = collection.get(ids=ids)
                    existing_ids = set(existing["ids"])
                    new_indices = [j for j, id_ in enumerate(ids) if id_ not in existing_ids]

                    if new_indices:
                        collection.add(
                            ids=[ids[j] for j in new_indices],
                            documents=[documents[j] for j in new_indices],
                            metadatas=[metadatas[j] for j in new_indices],
                        )
                except Exception:
                    collection.add(ids=ids, documents=documents, metadatas=metadatas)

            total_chunks += len(chunks)
            books_processed.append(book_path.name)
            print(f"  [OK] {book_path.name}: {len(chunks)} chunks")

        except Exception as e:
            print(f"  [ERR] Error processing {book_path.name}: {e}")

    return {
        "success": True,
        "message": f"Ingested {len(books_processed)} books with {total_chunks} total chunks",
        "books_processed": books_processed,
        "total_chunks": total_chunks,
    }


def retrieve_context(query: str, role: str = "", top_k: int = None) -> list[dict]:
    """
    Retrieve relevant knowledge chunks for a given query.
    
    Args:
        query: The search query (constructed from resume skills + role).
        role: Target role for filtered retrieval.
        top_k: Number of results to return.
        
    Returns:
        List of relevant chunks with metadata and relevance scores.
    """
    if top_k is None:
        top_k = settings.RAG_TOP_K

    collection = _get_collection()

    if collection.count() == 0:
        return []

    # Build where filter for role-specific books
    where_filter = None
    if role and role in ROLE_BOOK_TAGS:
        book_tags = ROLE_BOOK_TAGS[role]
        if len(book_tags) == 1:
            where_filter = {"book_tag": book_tags[0]}
        else:
            where_filter = {"book_tag": {"$in": book_tags}}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # Fallback: query without filter
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    if not results or not results["documents"] or not results["documents"][0]:
        return []

    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score: 1 - (distance / 2)
        similarity = 1 - (distance / 2)

        if similarity >= settings.RAG_SCORE_THRESHOLD:
            chunks.append({
                "text": doc,
                "metadata": meta,
                "similarity": round(similarity, 4),
                "source": meta.get("book_name", "Unknown"),
            })

    return chunks


def build_rag_queries(skills: list[str], role: str, domains: list[str] = None) -> list[str]:
    """
    Construct meaningful RAG queries from resume data and role.
    
    Strategy:
    - Combine skills with role-specific concepts
    - Generate domain-focused queries
    - Create cross-topic queries for deeper evaluation
    
    Returns:
        List of query strings for retrieval.
    """
    queries = []

    # Role-specific concept queries
    role_concepts = {
        "AI/ML Engineer": [
            "machine learning algorithms supervised unsupervised learning",
            "neural networks deep learning training optimization",
            "model evaluation cross validation bias variance tradeoff",
            "feature engineering selection dimensionality reduction",
            "gradient descent backpropagation loss functions",
        ],
        "Data Scientist": [
            "data analysis statistical methods hypothesis testing",
            "machine learning model selection evaluation metrics",
            "feature engineering data preprocessing pipelines",
            "regression classification clustering algorithms",
            "data visualization exploratory data analysis",
        ],
        "Backend Engineer": [
            "algorithms data structures complexity analysis",
            "system design scalability distributed systems",
            "database design optimization indexing",
            "machine learning fundamentals for backend engineers",
            "software engineering principles design patterns",
        ],
        "Full-Stack Developer": [
            "web development machine learning integration",
            "data processing pipelines and APIs",
            "machine learning fundamentals applications",
            "software architecture and system design",
            "algorithm design and problem solving",
        ],
    }

    # Add role-specific queries
    if role in role_concepts:
        queries.extend(role_concepts[role])

    # Skill-based queries — combine skills with ML concepts
    if skills:
        # Group skills into chunks of 3 for focused queries
        for i in range(0, min(len(skills), 9), 3):
            skill_group = skills[i:i + 3]
            query = f"{' '.join(skill_group)} concepts algorithms applications"
            queries.append(query)

    # Domain-specific queries
    if domains:
        for domain in domains[:3]:
            queries.append(f"{domain} machine learning applications techniques")

    return queries[:8]  # Limit to 8 queries max


# ─── Internal Helpers ────────────────────────────────────

def _extract_file_text(file_path: Path) -> str:
    """Extract text from a PDF or TXT file."""
    if file_path.suffix.lower() == ".txt":
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return file_path.read_text(encoding="latin-1")

    # PDF extraction
    import pdfplumber
    text_parts = []
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"PDF extraction error: {e}")
    return "\n\n".join(text_parts)


def _chunk_text(text: str, filename: str) -> list[dict]:
    """
    Chunk text into segments of ~500 tokens with 50-token overlap.
    
    Chunking strategy:
    - Split on paragraph boundaries first (preserves semantic context)
    - If a paragraph exceeds chunk size, split on sentence boundaries
    - Each chunk carries metadata: book name, tag, chunk index
    """
    book_tag = _identify_book(filename)
    book_name = filename.replace(".pdf", "")

    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20]

    chunks = []
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        # Estimate tokens (rough: 1 token ≈ 4 chars)
        para_tokens = len(para) // 4

        if para_tokens > settings.CHUNK_SIZE:
            # Split long paragraphs by sentences
            if current_chunk:
                chunks.append(_make_chunk(current_chunk, book_name, book_tag, chunk_index))
                chunk_index += 1
                current_chunk = ""

            sentences = re.split(r'(?<=[.!?])\s+', para)
            sentence_buffer = ""
            for sentence in sentences:
                if len((sentence_buffer + " " + sentence).strip()) // 4 > settings.CHUNK_SIZE:
                    if sentence_buffer:
                        chunks.append(_make_chunk(sentence_buffer, book_name, book_tag, chunk_index))
                        chunk_index += 1
                        # Overlap: keep last part of previous chunk
                        overlap_text = sentence_buffer.split('.')[-2:]  if '.' in sentence_buffer else []
                        sentence_buffer = '. '.join(overlap_text).strip() + " " + sentence if overlap_text else sentence
                    else:
                        sentence_buffer = sentence
                else:
                    sentence_buffer = (sentence_buffer + " " + sentence).strip()

            if sentence_buffer:
                current_chunk = sentence_buffer

        elif len((current_chunk + "\n\n" + para).strip()) // 4 > settings.CHUNK_SIZE:
            # Current chunk is full, save it and start new
            if current_chunk:
                chunks.append(_make_chunk(current_chunk, book_name, book_tag, chunk_index))
                chunk_index += 1
                # Overlap: keep last paragraph
                overlap = current_chunk.split('\n\n')[-1] if '\n\n' in current_chunk else ""
                current_chunk = (overlap + "\n\n" + para).strip() if overlap else para
            else:
                current_chunk = para
        else:
            current_chunk = (current_chunk + "\n\n" + para).strip()

    # Save final chunk
    if current_chunk and len(current_chunk) > 50:
        chunks.append(_make_chunk(current_chunk, book_name, book_tag, chunk_index))

    return chunks


def _make_chunk(text: str, book_name: str, book_tag: str, index: int) -> dict:
    """Create a chunk dict with ID and metadata."""
    chunk_id = hashlib.md5(f"{book_tag}_{index}_{text[:100]}".encode()).hexdigest()
    return {
        "id": chunk_id,
        "text": text.strip(),
        "metadata": {
            "book_name": book_name,
            "book_tag": book_tag,
            "chunk_index": index,
        },
    }


def _identify_book(filename: str) -> str:
    """Identify which book a PDF belongs to based on filename."""
    name_lower = filename.lower()
    for key, tag in BOOK_IDENTIFIERS.items():
        if key in name_lower:
            return tag
    return "unknown"
