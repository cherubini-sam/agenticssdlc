"""Pure vector retrieval with no LLM involvement. Connects lazily on first query."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document

from src.agents.agents_utils import (
    AGENTS_LIBRARIAN_AGENT_NAME,
    AGENTS_LIBRARIAN_DEFAULT_K,
    AGENTS_LIBRARIAN_LOG_RETRIEVED,
    AGENTS_LIBRARIAN_QUERY_LOG_TRUNCATION,
)
from src.rag.rag_retriever import RagRetriever
from src.rag.rag_vector_store import RagVectorStore

logger = logging.getLogger(__name__)


class AgentsLibrarian:
    """Top-k semantic retrieval from the vector store. No LLM calls."""

    agent_name: str = AGENTS_LIBRARIAN_AGENT_NAME

    def __init__(self, k: int = AGENTS_LIBRARIAN_DEFAULT_K) -> None:
        self._k = k
        self._retriever = None

    async def _agents_librarian_get_retriever(self) -> Any:
        """Vector store connection is deferred until the first query to avoid startup overhead."""

        if self._retriever is None:
            vector_store = await RagVectorStore.rag_vector_store_create()
            self._retriever = RagRetriever(vector_store, k=self._k)
        return self._retriever

    async def agents_librarian_retrieve(self, query: str) -> list[Document]:
        """Fetch top-k docs by semantic similarity."""

        retriever = await self._agents_librarian_get_retriever()
        docs = await retriever.rag_retriever_retrieve(query)
        logger.info(
            AGENTS_LIBRARIAN_LOG_RETRIEVED.format(
                count=len(docs), query=query[:AGENTS_LIBRARIAN_QUERY_LOG_TRUNCATION]
            )
        )
        return docs
