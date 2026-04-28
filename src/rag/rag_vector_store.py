"""Vector store abstraction that picks Qdrant or ChromaDB based on available credentials."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import chromadb
from langchain_chroma import Chroma
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    ScalarQuantization,
    ScalarQuantizationConfig,
    ScalarType,
    VectorParams,
)

from src.core.core_config import core_config_get_settings as get_settings
from src.rag.rag_embeddings import rag_embeddings_get_embeddings
from src.rag.rag_utils import (
    RAG_LOG_VECTOR_STORE_CHROMA_INIT,
    RAG_LOG_VECTOR_STORE_CHROMA_PATH_FALLBACK,
    RAG_LOG_VECTOR_STORE_CREATED_QDRANT,
    RAG_LOG_VECTOR_STORE_QDRANT_INIT,
    RAG_LOG_VECTOR_STORE_REBUILD_COMPLETE,
    RAG_LOG_VECTOR_STORE_RESET,
    RAG_LOG_VECTOR_STORE_RESET_START,
    RAG_RETRIEVER_DEFAULT_K,
    RAG_VECTOR_STORE_CHROMA_PATH,
    RAG_VECTOR_STORE_COLLECTION,
    RAG_VECTOR_STORE_DIM,
)

logger = logging.getLogger(__name__)

# chromadb 0.5.x ships with a posthog version that spams non-fatal errors; mute it
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

COLLECTION: str = RAG_VECTOR_STORE_COLLECTION
DIM: int = RAG_VECTOR_STORE_DIM


async def _rag_vector_store_create_qdrant(settings: Any, embeddings: Any) -> "RagVectorStore":
    """Provision (if needed) and connect to the Qdrant collection."""

    loop = asyncio.get_running_loop()
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )

    collections = await loop.run_in_executor(None, client.get_collections)
    existing = [c.name for c in collections.collections]
    if COLLECTION not in existing:
        try:
            await loop.run_in_executor(
                None,
                lambda: client.create_collection(
                    collection_name=COLLECTION,
                    vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
                    quantization_config=ScalarQuantization(
                        scalar=ScalarQuantizationConfig(
                            type=ScalarType.INT8,
                            always_ram=True,
                        )
                    ),
                ),
            )
            logger.info(RAG_LOG_VECTOR_STORE_CREATED_QDRANT, COLLECTION)
        except UnexpectedResponse:
            pass

    store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION,
        embedding=embeddings,
    )
    logger.info(RAG_LOG_VECTOR_STORE_QDRANT_INIT, settings.qdrant_url)
    return RagVectorStore(store, "qdrant", _client=client)


async def _rag_vector_store_create_chroma(embeddings: Any) -> "RagVectorStore":
    """Create a persistent ChromaDB-backed store."""

    try:
        chroma_path = get_settings().chroma_path
    except Exception as e:
        logger.warning(RAG_LOG_VECTOR_STORE_CHROMA_PATH_FALLBACK, e)
        chroma_path = RAG_VECTOR_STORE_CHROMA_PATH

    client = chromadb.PersistentClient(
        path=chroma_path,
        settings=chromadb.Settings(anonymized_telemetry=False),
    )
    store = Chroma(
        client=client,
        collection_name=COLLECTION,
        embedding_function=embeddings,
    )
    logger.info(RAG_LOG_VECTOR_STORE_CHROMA_INIT, chroma_path)
    return RagVectorStore(store, "chroma", _client=client)


class RagVectorStore:
    """Thin wrapper that normalises the Qdrant / ChromaDB interface."""

    def __init__(self, store: Any, primary: str, *, _client: Any = None) -> None:
        self._store = store
        self._client = _client
        self.primary = primary

    @classmethod
    async def rag_vector_store_create(cls) -> "RagVectorStore":
        """Pick backend based on config: Qdrant if QDRANT_URL is set, ChromaDB otherwise."""

        settings = get_settings()
        embeddings = rag_embeddings_get_embeddings()

        if settings.qdrant_url:
            return await _rag_vector_store_create_qdrant(settings, embeddings)
        return await _rag_vector_store_create_chroma(embeddings)

    async def rag_vector_store_add_documents(self, docs: list) -> int:
        """Add documents asynchronously regardless of backend."""

        if hasattr(self._store, "aadd_documents"):
            await self._store.aadd_documents(docs)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._store.add_documents, docs)
        return len(docs)

    def rag_vector_store_get_retriever(self, k: int = RAG_RETRIEVER_DEFAULT_K) -> Any:
        """Return a Qdrant / ChromaDB retriever."""

        return self._store.as_retriever(search_kwargs={"k": k})

    async def rag_vector_store_reset(self) -> None:
        """Drop and recreate the collection, wiping all stored vectors."""

        loop = asyncio.get_running_loop()

        if self.primary == "qdrant":
            client: QdrantClient = self._client
            await loop.run_in_executor(None, client.delete_collection, COLLECTION)
            await loop.run_in_executor(
                None,
                lambda: client.create_collection(
                    collection_name=COLLECTION,
                    vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
                    quantization_config=ScalarQuantization(
                        scalar=ScalarQuantizationConfig(
                            type=ScalarType.INT8,
                            always_ram=True,
                        )
                    ),
                ),
            )
        elif self.primary == "chroma":
            chroma_client: chromadb.ClientAPI = self._client
            await loop.run_in_executor(None, chroma_client.delete_collection, COLLECTION)
            embeddings = rag_embeddings_get_embeddings()
            self._store = Chroma(
                client=chroma_client,
                collection_name=COLLECTION,
                embedding_function=embeddings,
            )

        logger.info(RAG_LOG_VECTOR_STORE_RESET, COLLECTION, self.primary)


_instance: RagVectorStore | None = None
_init_lock: asyncio.Lock = asyncio.Lock()


async def rag_vector_store_get_instance() -> RagVectorStore:
    """Return the shared RagVectorStore singleton, creating it on first call."""

    global _instance
    if _instance is not None:
        return _instance
    async with _init_lock:
        if _instance is None:
            _instance = await RagVectorStore.rag_vector_store_create()
    return _instance


async def rag_vector_store_reset_and_rebuild(base_path: str = ".agent/rag/") -> int:
    """Reset the vector store and ingest manifest, then re-ingest from scratch."""

    from src.rag.rag_ingestion import rag_ingestion_ingest, rag_ingestion_reset_manifest

    store = await rag_vector_store_get_instance()
    logger.info(RAG_LOG_VECTOR_STORE_RESET_START, store.primary)

    await store.rag_vector_store_reset()
    rag_ingestion_reset_manifest()

    count = await rag_ingestion_ingest(store, base_path)
    logger.info(RAG_LOG_VECTOR_STORE_REBUILD_COMPLETE, count)
    return count
