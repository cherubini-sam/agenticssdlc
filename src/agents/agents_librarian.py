"""Vector retrieval + LLM synthesis. Connects to the vector store lazily on first query."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_LIBRARIAN_AGENT_NAME,
    AGENTS_LIBRARIAN_DEFAULT_K,
    AGENTS_LIBRARIAN_DOC_PATHS,
    AGENTS_LIBRARIAN_LOG_RETRIEVED,
    AGENTS_LIBRARIAN_QUERY_LOG_TRUNCATION,
    AGENTS_LIBRARIAN_SYSTEM_PROMPT,
)
from src.rag.rag_retriever import RagRetriever
from src.rag.rag_vector_store import rag_vector_store_get_instance

logger = logging.getLogger(__name__)


class AgentsLibrarian(AgentsBase):
    """Top-k semantic retrieval from the vector store, followed by LLM context synthesis."""

    agent_name: str = AGENTS_LIBRARIAN_AGENT_NAME
    role_doc_paths: list[str] = AGENTS_LIBRARIAN_DOC_PATHS

    def __init__(self, k: int = AGENTS_LIBRARIAN_DEFAULT_K) -> None:
        """Set up the librarian with a configurable top-k retrieval limit.

        :param k: Number of top documents to retrieve per query.
        :type k: int
        """
        super().__init__()
        self._k = k
        self._retriever: RagRetriever | None = None

    async def _agents_librarian_get_retriever(self) -> Any:
        """Retriever is built once per instance; vector store is a process-wide singleton.

        :return: Configured RagRetriever instance.
        :rtype: Any
        """

        if self._retriever is None:
            vector_store = await rag_vector_store_get_instance()
            self._retriever = RagRetriever(vector_store, k=self._k)
        return self._retriever

    async def agents_librarian_retrieve(self, query: str) -> str:
        """Fetch top-k docs by semantic similarity, then synthesize via LLM.

        :param query: User task string used as the semantic search query.
        :type query: str
        :return: LLM-synthesized context string ready for downstream agents.
        :rtype: str
        """

        retriever = await self._agents_librarian_get_retriever()
        docs = await retriever.rag_retriever_retrieve(query)
        logger.info(
            AGENTS_LIBRARIAN_LOG_RETRIEVED.format(
                count=len(docs), query=query[:AGENTS_LIBRARIAN_QUERY_LOG_TRUNCATION]
            )
        )

        raw_text: str = "\n\n".join(d.page_content for d in docs) if docs else ""

        system_prompt: str = self._agents_base_build_system_prompt(AGENTS_LIBRARIAN_SYSTEM_PROMPT)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=raw_text or query),
        ]
        try:
            synthesized: str = await self._agents_base_call_llm(messages)
        except Exception:
            synthesized = raw_text
        return synthesized
