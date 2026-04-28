"""Shared constants for the RAG subsystem."""

from __future__ import annotations

# Vector store

RAG_VECTOR_STORE_COLLECTION: str = "agentics_sdlc_kb"
# 1024 = fixed output dimensionality of BAAI/bge-large-en-v1.5 (cannot be changed)
RAG_VECTOR_STORE_DIM: int = 1024
# Default fallback path; overridden by CoreSettings.chroma_path when config is available
RAG_VECTOR_STORE_CHROMA_PATH: str = "./data/chroma"

# Embeddings

RAG_EMBEDDINGS_MODEL_NAME: str = "BAAI/bge-large-en-v1.5"
# 64 samples per batch balances throughput vs. RAM; increase on GPU, decrease on CPU-only
RAG_EMBEDDINGS_BATCH_SIZE: int = 64

# Ingestion

# 2000 chars ≈ 500 tokens — Microsoft Azure benchmark for RAG; sized to BGE-large 512-token ceiling.
RAG_INGESTION_CHUNK_SIZE: int = 2000
# 400-char overlap (20%) preserves cross-boundary context without excessive duplication.
RAG_INGESTION_CHUNK_OVERLAP: int = 400

# Parent directories excluded from knowledge-base ingestion.
RAG_INGESTION_EXCLUDED_DIRS: frozenset[str] = frozenset({"artifacts"})

# Maps parent directory names to metadata category tags
RAG_INGESTION_CATEGORY_MAP: dict[str, str] = {
    "protocols": "protocol",
    "roles": "role",
    "rules": "rule",
    "skills": "skill",
}

# Splitting priority: prefer paragraph/line breaks before sub-word splits
RAG_INGESTION_SEPARATORS: list[str] = ["\n\n", "\n", "```", " ", ""]

# Persistent manifest for incremental ingestion.
RAG_INGEST_MANIFEST_PATH: str = "data/rag_ingest_manifest.json"

# Retriever

# Top-4 docs injects ~1000 tokens of context — sufficient without overloading LLM window
RAG_RETRIEVER_DEFAULT_K: int = 4
RAG_RETRIEVER_QUERY_LOG_TRUNCATION: int = 50
# 30s protects against a stuck vector DB; Qdrant typically responds in < 100ms
RAG_RETRIEVER_TIMEOUT_SECONDS: int = 30
# 0.0 = no filtering (backward-compatible default); set > 0 to drop low-relevance results
RAG_RETRIEVER_DEFAULT_SCORE_THRESHOLD: float = 0.0

# Metadata keys

RAG_KEY_CATEGORY: str = "category"
RAG_KEY_FILENAME: str = "filename"
RAG_KEY_SOURCE: str = "source"
# SHA-256 digest of chunk content — used for intra-batch and cross-run deduplication
RAG_KEY_CHUNK_HASH: str = "chunk_hash"

# Log message templates (use %s positional args for lazy evaluation)

RAG_LOG_INGESTION_LOADED: str = "Loaded %d documents from %s"
RAG_LOG_INGESTION_STATS: str = "Ingestion stats — loaded: %d, skipped: %d, errors: %d"
RAG_LOG_INGESTION_CATEGORY_UNMAPPED: str = "Directory '%s' not in CATEGORY_MAP; using 'general'"
RAG_LOG_INGESTION_LOAD_ERROR: str = "Failed to load %s: %s"
RAG_LOG_INGESTION_CHUNKED: str = "Split %d documents into %d chunks"
RAG_LOG_INGESTION_SKIPPED: str = "Skipped %d already-ingested chunks (manifest hit)"
RAG_LOG_INGESTION_COMPLETE: str = "Ingested %d new chunks into %s"

RAG_LOG_VECTOR_STORE_CHROMA_INIT: str = "Initializing ChromaDB at %s"
RAG_LOG_VECTOR_STORE_QDRANT_INIT: str = "Initializing Qdrant client at %s"
RAG_LOG_VECTOR_STORE_CREATED_QDRANT: str = "Created Qdrant collection: %s"
RAG_LOG_VECTOR_STORE_RESET: str = "Vector store collection '%s' reset on backend '%s'"
RAG_LOG_VECTOR_STORE_RESET_START: str = "Starting full reset and rebuild of vector store (%s)."
RAG_LOG_VECTOR_STORE_REBUILD_COMPLETE: str = "Rebuild complete — %d chunks ingested."
RAG_LOG_VECTOR_STORE_NO_NEW_CHUNKS: str = "No new chunks to ingest — knowledge base is up to date."
RAG_LOG_VECTOR_STORE_CHROMA_PATH_FALLBACK: str = (
    "Failed to read chroma_path from settings (%s) — using default."
)
RAG_LOG_VECTOR_STORE_MANIFEST_DELETED: str = "Ingest manifest deleted: %s"
RAG_LOG_VECTOR_STORE_MANIFEST_READ_ERROR: str = (
    "Failed to read ingest manifest at %s: %s — starting fresh"
)

RAG_LOG_RETRIEVER_EMPTY_QUERY: str = "Empty query passed to retriever; returning no results."
RAG_LOG_RETRIEVER_TIMEOUT: str = "Retrieval timed out after %ds | query: '%s...'"
RAG_LOG_RETRIEVER_ERROR: str = "Retrieval failed: %s"
RAG_LOG_RETRIEVER_SUCCESS: str = "Retrieved %d docs | query: '%s...'"
