"""Shared constants for the RAG subsystem."""

from __future__ import annotations

# --- Vector store ---

RAG_VECTOR_STORE_COLLECTION: str = "agentics_sdlc_kb"
RAG_VECTOR_STORE_DIM: int = 1024  # BGE-large output dimensionality
RAG_VECTOR_STORE_CHROMA_PATH: str = "./data/chroma"

# --- Embeddings ---

RAG_EMBEDDINGS_MODEL_NAME: str = "BAAI/bge-large-en-v1.5"
RAG_EMBEDDINGS_BATCH_SIZE: int = 64

# --- Ingestion ---

RAG_INGESTION_CHUNK_SIZE: int = 1000
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

# --- Retriever ---

RAG_RETRIEVER_DEFAULT_K: int = 4
RAG_RETRIEVER_QUERY_LOG_TRUNCATION: int = 50
RAG_RETRIEVER_TIMEOUT_SECONDS: int = 30

# --- Metadata keys ---

RAG_KEY_CATEGORY: str = "category"
RAG_KEY_FILENAME: str = "filename"
RAG_KEY_SOURCE: str = "source"

# --- Log message templates ---

RAG_LOG_INGESTION_LOADED: str = "Loaded {count} documents from {path}"
RAG_LOG_INGESTION_CHUNKED: str = "Split {docs} documents into {chunks} chunks"
RAG_LOG_INGESTION_COMPLETE: str = "Ingested {count} chunks into {store}"

RAG_LOG_VECTOR_STORE_CHROMA_INIT: str = "Initializing ChromaDB at %s"
RAG_LOG_VECTOR_STORE_QDRANT_INIT: str = "Initializing Qdrant client at %s"
RAG_LOG_VECTOR_STORE_CREATED_QDRANT: str = "Created Qdrant collection: %s"

RAG_LOG_RETRIEVER_TIMEOUT: str = "Retrieval timed out after {timeout}s | query: '{query}...'"
RAG_LOG_RETRIEVER_ERROR: str = "Retrieval failed: {error}"
RAG_LOG_RETRIEVER_SUCCESS: str = "Retrieved {count} docs | query: '{query}...'"
