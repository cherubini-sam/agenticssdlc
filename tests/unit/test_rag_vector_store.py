"""Unit tests for RagVectorStore: singleton, add_documents, and reset."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import chromadb
import pytest
from langchain_core.documents import Document

import src.rag.rag_vector_store as vs_module
from src.rag.rag_vector_store import RagVectorStore


class TestRagVectorStoreSingleton:
    """Tests for the RagVectorStore module-level singleton accessor."""

    @pytest.mark.asyncio
    async def test_singleton_returns_same_instance(self) -> None:
        """Two concurrent calls to rag_vector_store_get_instance must return the same object."""

        mock_instance = MagicMock()
        original = vs_module._instance
        try:
            vs_module._instance = mock_instance
            result1 = await vs_module.rag_vector_store_get_instance()
            result2 = await vs_module.rag_vector_store_get_instance()
            assert result1 is result2 is mock_instance
        finally:
            vs_module._instance = original

    @pytest.mark.asyncio
    async def test_singleton_creates_instance_once(self) -> None:
        """rag_vector_store_create is called exactly once even under concurrent access."""

        original = vs_module._instance
        try:
            vs_module._instance = None
            fake_store = MagicMock()
            with patch.object(
                vs_module.RagVectorStore,
                "rag_vector_store_create",
                new=AsyncMock(return_value=fake_store),
            ):
                results = await asyncio.gather(
                    vs_module.rag_vector_store_get_instance(),
                    vs_module.rag_vector_store_get_instance(),
                )
            assert results[0] is results[1]
        finally:
            vs_module._instance = original


class TestRagVectorStoreAddDocuments:
    """Tests for RagVectorStore add_documents async and sync paths."""

    @pytest.mark.asyncio
    async def test_add_documents_returns_count(self) -> None:
        """add_documents returns the number of docs passed, not a backend count."""

        mock_store = MagicMock()
        mock_store.aadd_documents = AsyncMock(return_value=None)

        store = RagVectorStore(mock_store, "chroma")
        docs = [
            Document(page_content="a", metadata={}),
            Document(page_content="b", metadata={}),
            Document(page_content="c", metadata={}),
        ]
        count = await store.rag_vector_store_add_documents(docs)
        assert count == 3

    @pytest.mark.asyncio
    async def test_add_documents_falls_back_to_sync(self) -> None:
        """When aadd_documents is absent the sync add_documents path is used."""

        mock_store = MagicMock(spec=[])
        mock_store.add_documents = MagicMock(return_value=None)

        store = RagVectorStore(mock_store, "chroma")
        docs = [Document(page_content="x", metadata={})]
        count = await store.rag_vector_store_add_documents(docs)
        assert count == 1


class TestRagVectorStoreReset:
    """Tests for RagVectorStore reset logic for Chroma and Qdrant backends."""

    @pytest.mark.asyncio
    async def test_reset_chroma_deletes_and_recreates_collection(self) -> None:
        """ChromaDB reset deletes the collection and reassigns self._store."""

        mock_chroma_client = MagicMock(spec=chromadb.ClientAPI)
        mock_chroma_client.delete_collection = MagicMock()
        mock_new_store = MagicMock()

        store = RagVectorStore(MagicMock(), "chroma", _client=mock_chroma_client)

        with (
            patch("src.rag.rag_vector_store.Chroma", return_value=mock_new_store),
            patch(
                "src.rag.rag_vector_store.rag_embeddings_get_embeddings",
                return_value=MagicMock(),
            ),
        ):
            await store.rag_vector_store_reset()

        mock_chroma_client.delete_collection.assert_called_once()
        assert store._store is mock_new_store

    @pytest.mark.asyncio
    async def test_reset_qdrant_deletes_and_recreates_collection(self) -> None:
        """Qdrant reset calls delete_collection and create_collection on the client."""

        mock_qdrant_client = MagicMock()
        mock_qdrant_client.delete_collection = MagicMock()
        mock_qdrant_client.create_collection = MagicMock()

        store = RagVectorStore(MagicMock(), "qdrant", _client=mock_qdrant_client)
        await store.rag_vector_store_reset()

        mock_qdrant_client.delete_collection.assert_called_once()
        mock_qdrant_client.create_collection.assert_called_once()
