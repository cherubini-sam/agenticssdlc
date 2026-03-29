"""Dense retrieval over HNSW (Qdrant) or flat index (ChromaDB)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.documents import Document

from src.rag.rag_utils import (
    RAG_LOG_RETRIEVER_ERROR,
    RAG_LOG_RETRIEVER_SUCCESS,
    RAG_LOG_RETRIEVER_TIMEOUT,
    RAG_RETRIEVER_DEFAULT_K,
    RAG_RETRIEVER_QUERY_LOG_TRUNCATION,
    RAG_RETRIEVER_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class RagRetriever:
    """
    Top-k semantic retrieval backed by BGE-large embeddings.
    No BM25 or cross-encoder reranking: overkill at our current doc scale (see ADR-003).
    """

    def __init__(self, vector_store: Any, k: int = RAG_RETRIEVER_DEFAULT_K) -> None:
        self.retriever = vector_store.rag_vector_store_get_retriever(k=k)
        self.logger = logging.getLogger("rag.rag_retriever")

    async def rag_retriever_retrieve(self, query: str) -> list[Document]:
        # Wrapping in wait_for so a stuck vector DB call doesn't block the whole request
        try:
            docs = await asyncio.wait_for(
                self.retriever.ainvoke(query),
                timeout=RAG_RETRIEVER_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            self.logger.warning(
                RAG_LOG_RETRIEVER_TIMEOUT.format(
                    timeout=RAG_RETRIEVER_TIMEOUT_SECONDS,
                    query=query[:RAG_RETRIEVER_QUERY_LOG_TRUNCATION],
                )
            )
            return []
        except Exception as exc:
            self.logger.error(RAG_LOG_RETRIEVER_ERROR.format(error=exc), exc_info=True)
            return []
        self.logger.info(
            RAG_LOG_RETRIEVER_SUCCESS.format(
                count=len(docs), query=query[:RAG_RETRIEVER_QUERY_LOG_TRUNCATION]
            )
        )
        return docs
