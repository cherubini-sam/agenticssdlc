"""Dense retrieval over HNSW (Qdrant) or flat index (ChromaDB)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.documents import Document

from src.rag.rag_utils import (
    RAG_LOG_RETRIEVER_EMPTY_QUERY,
    RAG_LOG_RETRIEVER_ERROR,
    RAG_LOG_RETRIEVER_SUCCESS,
    RAG_LOG_RETRIEVER_TIMEOUT,
    RAG_RETRIEVER_DEFAULT_K,
    RAG_RETRIEVER_DEFAULT_SCORE_THRESHOLD,
    RAG_RETRIEVER_QUERY_LOG_TRUNCATION,
    RAG_RETRIEVER_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class RagRetriever:
    """Top-k semantic retrieval backed by BGE-large embeddings."""

    def __init__(self, vector_store: Any, k: int = RAG_RETRIEVER_DEFAULT_K) -> None:
        self._vector_store = vector_store
        self._k = k
        self.retriever = vector_store.rag_vector_store_get_retriever(k=k)

    async def rag_retriever_retrieve(
        self,
        query: str,
        *,
        k: int | None = None,
        score_threshold: float = RAG_RETRIEVER_DEFAULT_SCORE_THRESHOLD,
    ) -> list[Document]:
        """Return up to *k* semantically relevant documents for *query*."""

        if not query.strip():
            logger.warning(RAG_LOG_RETRIEVER_EMPTY_QUERY)
            return []

        # Use a per-call retriever when k differs from the cached one
        retriever = (
            self._vector_store.rag_vector_store_get_retriever(k=k)
            if k is not None and k != self._k
            else self.retriever
        )

        # Wrap in wait_for so a stuck vector DB call doesn't block the whole request
        try:
            docs = await asyncio.wait_for(
                retriever.ainvoke(query),
                timeout=RAG_RETRIEVER_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(
                RAG_LOG_RETRIEVER_TIMEOUT,
                RAG_RETRIEVER_TIMEOUT_SECONDS,
                query[:RAG_RETRIEVER_QUERY_LOG_TRUNCATION],
            )
            return []
        except Exception as exc:
            logger.error(RAG_LOG_RETRIEVER_ERROR, exc, exc_info=True)
            return []

        # Best-effort score filtering (only effective when backend sets metadata["score"])
        if score_threshold > 0.0:
            docs = [d for d in docs if d.metadata.get("score", 1.0) >= score_threshold]

        logger.info(
            RAG_LOG_RETRIEVER_SUCCESS,
            len(docs),
            query[:RAG_RETRIEVER_QUERY_LOG_TRUNCATION],
        )
        return docs
