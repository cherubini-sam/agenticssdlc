"""Shared constants for the RAG subsystem."""

from __future__ import annotations

# Vector store

RAG_VECTOR_STORE_COLLECTION: str = "agentics_sdlc_kb"
# 1024 = fixed output dimensionality of BAAI/bge-large-en-v1.5 (cannot be changed)
RAG_VECTOR_STORE_DIM: int = 1024
RAG_VECTOR_STORE_CHROMA_PATH: str = "./data/chroma"

# Embeddings

RAG_EMBEDDINGS_MODEL_NAME: str = "BAAI/bge-large-en-v1.5"
# 64 samples per batch balances throughput vs. RAM; increase on GPU, decrease on CPU-only
RAG_EMBEDDINGS_BATCH_SIZE: int = 64

# Ingestion

# 1000 chars ≈ 250 words — good semantic granularity for paragraph-level retrieval
RAG_INGESTION_CHUNK_SIZE: int = 1000
# 200-char overlap (20%) preserves cross-boundary context without excessive duplication
RAG_INGESTION_CHUNK_OVERLAP: int = 200

# Maps parent directory names to metadata category tags
RAG_INGESTION_CATEGORY_MAP: dict[str, str] = {
    "protocols": "protocol",
    "roles": "role",
    "rules": "rule",
    "shards": "shard",
    "skills": "skill",
    "artifacts": "artifact",
}

# Splitting priority: prefer paragraph breaks, then lines, then code fences, etc.
RAG_INGESTION_SEPARATORS: list[str] = ["\n\n", "\n", "```", ".", " ", ""]

# Retriever

# Top-4 docs injects ~1000 tokens of context — sufficient without overloading LLM window
RAG_RETRIEVER_DEFAULT_K: int = 4
RAG_RETRIEVER_QUERY_LOG_TRUNCATION: int = 50
# 30s protects against a stuck vector DB; Qdrant typically responds in < 100ms
RAG_RETRIEVER_TIMEOUT_SECONDS: int = 30

# Metadata keys

RAG_KEY_CATEGORY: str = "category"
RAG_KEY_FILENAME: str = "filename"
RAG_KEY_SOURCE: str = "source"
# SHA-256 digest of chunk content — used for intra-batch deduplication
RAG_KEY_CHUNK_HASH: str = "chunk_hash"

# Log message templates

RAG_LOG_INGESTION_LOADED: str = "Loaded {count} documents from {path}"
RAG_LOG_INGESTION_STATS: str = (
    "Ingestion stats — loaded: {loaded}, skipped: {skipped}, errors: {errors}"
)
RAG_LOG_INGESTION_CATEGORY_UNMAPPED: str = "Directory '%s' not in CATEGORY_MAP; using 'general'"
RAG_LOG_INGESTION_CHUNKED: str = "Split {docs} documents into {chunks} chunks"
RAG_LOG_INGESTION_COMPLETE: str = "Ingested {count} chunks into {store}"

RAG_LOG_VECTOR_STORE_CHROMA_INIT: str = "Initializing ChromaDB at %s"
RAG_LOG_VECTOR_STORE_QDRANT_INIT: str = "Initializing Qdrant client at %s"
RAG_LOG_VECTOR_STORE_CREATED_QDRANT: str = "Created Qdrant collection: %s"

RAG_LOG_RETRIEVER_EMPTY_QUERY: str = "Empty query passed to retriever; returning no results."
RAG_LOG_RETRIEVER_TIMEOUT: str = "Retrieval timed out after {timeout}s | query: '{query}...'"
RAG_LOG_RETRIEVER_ERROR: str = "Retrieval failed: {error}"
RAG_LOG_RETRIEVER_SUCCESS: str = "Retrieved {count} docs | query: '{query}...'"
