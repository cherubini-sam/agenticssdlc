"""RagRetriever dense top-k retrieval and error handling."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.documents import Document

import src.rag.rag_retriever as retriever_module
from src.rag.rag_retriever import RagRetriever


class TestRagRetriever:
    """Tests for RagRetriever top-k retrieval, error handling, and filtering."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_documents(self) -> None:
        """RagRetriever must return a list of Documents."""

        mock_docs = [
            Document(page_content="Python is a language", metadata={"source": "test"}),
            Document(page_content="FastAPI is a framework", metadata={"source": "test"}),
        ]
        mock_base_retriever = AsyncMock()
        mock_base_retriever.ainvoke = AsyncMock(return_value=mock_docs)
        mock_vector_store = MagicMock()
        mock_vector_store.rag_vector_store_get_retriever = MagicMock(
            return_value=mock_base_retriever
        )

        retriever = RagRetriever(mock_vector_store, k=4)
        results = await retriever.rag_retriever_retrieve("Python programming")
        assert len(results) == 2
        assert all(isinstance(doc, Document) for doc in results)

    @pytest.mark.asyncio
    async def test_retrieve_empty_query_returns_empty(self) -> None:
        """Blank or whitespace-only query must return [] without calling the backend."""

        mock_base_retriever = AsyncMock()
        mock_base_retriever.ainvoke = AsyncMock(return_value=[])
        mock_vector_store = MagicMock()
        mock_vector_store.rag_vector_store_get_retriever = MagicMock(
            return_value=mock_base_retriever
        )

        retriever = RagRetriever(mock_vector_store)
        result = await retriever.rag_retriever_retrieve("   ")
        assert result == []
        mock_base_retriever.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_timeout_returns_empty(self) -> None:
        """A TimeoutError from the vector DB must return [] gracefully."""

        async def _slow(*_):
            await asyncio.sleep(999)

        mock_base_retriever = MagicMock()
        mock_base_retriever.ainvoke = _slow
        mock_vector_store = MagicMock()
        mock_vector_store.rag_vector_store_get_retriever = MagicMock(
            return_value=mock_base_retriever
        )

        retriever = RagRetriever(mock_vector_store)
        original = retriever_module.RAG_RETRIEVER_TIMEOUT_SECONDS
        retriever_module.RAG_RETRIEVER_TIMEOUT_SECONDS = 0.001
        try:
            result = await retriever.rag_retriever_retrieve("test query")
        finally:
            retriever_module.RAG_RETRIEVER_TIMEOUT_SECONDS = original
        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_exception_returns_empty(self) -> None:
        """Any unexpected backend error must return [] without propagating."""

        mock_base_retriever = AsyncMock()
        mock_base_retriever.ainvoke = AsyncMock(side_effect=Exception("vector store unavailable"))
        mock_vector_store = MagicMock()
        mock_vector_store.rag_vector_store_get_retriever = MagicMock(
            return_value=mock_base_retriever
        )

        retriever = RagRetriever(mock_vector_store)
        result = await retriever.rag_retriever_retrieve("test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_per_query_k_override(self) -> None:
        """Passing k= to rag_retriever_retrieve creates a new retriever for that call."""

        docs_2 = [Document(page_content=f"doc{i}", metadata={}) for i in range(2)]
        mock_override_retriever = AsyncMock()
        mock_override_retriever.ainvoke = AsyncMock(return_value=docs_2)
        mock_default_retriever = AsyncMock()
        mock_default_retriever.ainvoke = AsyncMock(return_value=[])

        def _get_retriever(k):
            return mock_override_retriever if k == 2 else mock_default_retriever

        mock_vector_store = MagicMock()
        mock_vector_store.rag_vector_store_get_retriever = MagicMock(side_effect=_get_retriever)

        retriever = RagRetriever(mock_vector_store, k=4)
        results = await retriever.rag_retriever_retrieve("query", k=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_score_threshold_filters_low_relevance(self) -> None:
        """Documents with score below the threshold must be excluded from results."""

        mock_docs = [
            Document(page_content="high relevance", metadata={"score": 0.9}),
            Document(page_content="low relevance", metadata={"score": 0.3}),
            Document(page_content="no score key", metadata={}),
        ]
        mock_base_retriever = AsyncMock()
        mock_base_retriever.ainvoke = AsyncMock(return_value=mock_docs)
        mock_vector_store = MagicMock()
        mock_vector_store.rag_vector_store_get_retriever = MagicMock(
            return_value=mock_base_retriever
        )

        retriever = RagRetriever(mock_vector_store)
        results = await retriever.rag_retriever_retrieve("query", score_threshold=0.5)
        contents = [d.page_content for d in results]
        assert "low relevance" not in contents
        assert "high relevance" in contents
        assert "no score key" in contents
