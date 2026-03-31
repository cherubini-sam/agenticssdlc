"""AgentsLibrarian lazy retriever init, caching, and default k."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document


class TestLibrarianAgent:
    @pytest.mark.asyncio
    async def test_retrieve_returns_documents(self) -> None:
        from agents.agents_librarian import AgentsLibrarian

        mock_docs = [
            Document(page_content="doc one", metadata={}),
            Document(page_content="doc two", metadata={}),
        ]
        mock_retriever = MagicMock()
        mock_retriever.rag_retriever_retrieve = AsyncMock(return_value=mock_docs)

        agent = AgentsLibrarian()
        agent._retriever = mock_retriever

        result = await agent.agents_librarian_retrieve("how to build a REST API")
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(d, Document) for d in result)

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self) -> None:
        from agents.agents_librarian import AgentsLibrarian

        mock_retriever = MagicMock()
        mock_retriever.rag_retriever_retrieve = AsyncMock(return_value=[])

        agent = AgentsLibrarian()
        agent._retriever = mock_retriever

        result = await agent.agents_librarian_retrieve("unknown query")
        assert result == []

    @pytest.mark.asyncio
    async def test_retriever_lazy_init(self) -> None:
        from agents.agents_librarian import AgentsLibrarian

        mock_docs = [Document(page_content="lazy doc", metadata={})]
        mock_retriever = MagicMock()
        mock_retriever.rag_retriever_retrieve = AsyncMock(return_value=mock_docs)

        mock_vs = MagicMock()

        with (
            patch(
                "agents.agents_librarian.rag_vector_store_get_instance",
                new_callable=AsyncMock,
                return_value=mock_vs,
            ),
            patch(
                "agents.agents_librarian.RagRetriever",
                return_value=mock_retriever,
            ),
        ):
            agent = AgentsLibrarian(k=3)
            # retriever shouldn't exist yet -- it's created on first call
            assert agent._retriever is None
            result = await agent.agents_librarian_retrieve("test query")
            assert agent._retriever is mock_retriever
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_retriever_reuses_cached_instance(self) -> None:
        from agents.agents_librarian import AgentsLibrarian

        mock_retriever = MagicMock()
        mock_retriever.rag_retriever_retrieve = AsyncMock(return_value=[])

        agent = AgentsLibrarian()
        agent._retriever = mock_retriever

        await agent.agents_librarian_retrieve("first query")
        await agent.agents_librarian_retrieve("second query")

        # same instance, no re-init
        assert agent._retriever is mock_retriever
        assert mock_retriever.rag_retriever_retrieve.call_count == 2

    def test_default_k(self) -> None:
        from agents.agents_librarian import AgentsLibrarian
        from agents.agents_utils import AGENTS_LIBRARIAN_DEFAULT_K

        agent = AgentsLibrarian()
        assert agent._k == AGENTS_LIBRARIAN_DEFAULT_K

    def test_custom_k(self) -> None:
        from agents.agents_librarian import AgentsLibrarian

        agent = AgentsLibrarian(k=10)
        assert agent._k == 10

    def test_agent_name(self) -> None:
        from agents.agents_librarian import AgentsLibrarian

        assert AgentsLibrarian.agent_name == "LIBRARIAN"
