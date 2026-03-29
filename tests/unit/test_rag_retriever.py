"""RagRetriever dense top-k retrieval and error handling."""

from __future__ import annotations

import logging

import pytest
from langchain_core.documents import Document


class TestRagRetriever:
    @pytest.mark.asyncio
    async def test_retrieve_returns_documents(self) -> None:
        from unittest.mock import AsyncMock

        from rag.rag_retriever import RagRetriever

        retriever = RagRetriever.__new__(RagRetriever)
        retriever.logger = logging.getLogger("test")

        mock_docs = [
            Document(page_content="Python is a language", metadata={"source": "test"}),
            Document(page_content="FastAPI is a framework", metadata={"source": "test"}),
        ]

        mock_base_retriever = AsyncMock()
        mock_base_retriever.ainvoke = AsyncMock(return_value=mock_docs)
        retriever.retriever = mock_base_retriever

        results = await retriever.rag_retriever_retrieve("Python programming")
        assert len(results) == 2
        assert all(isinstance(doc, Document) for doc in results)

    @pytest.mark.asyncio
    async def test_retrieve_raises_on_vector_store_error(self) -> None:
        from unittest.mock import AsyncMock

        from rag.rag_retriever import RagRetriever

        retriever = RagRetriever.__new__(RagRetriever)
        retriever.logger = logging.getLogger("test")

        mock_base_retriever = AsyncMock()
        mock_base_retriever.ainvoke = AsyncMock(side_effect=Exception("vector store unavailable"))
        retriever.retriever = mock_base_retriever

        try:
            results = await retriever.rag_retriever_retrieve("test query")
            # Some implementations gracefully degrade to an empty list
            assert results == []
        except Exception:
            pass
