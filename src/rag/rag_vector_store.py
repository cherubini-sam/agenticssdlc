"""Vector store abstraction that picks Qdrant or ChromaDB based on available credentials."""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from langchain_chroma import Chroma
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
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
    RAG_LOG_VECTOR_STORE_CREATED_QDRANT,
    RAG_LOG_VECTOR_STORE_QDRANT_INIT,
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


class RagVectorStore:
    """Thin wrapper that normalises the Qdrant / ChromaDB interface for the rest of the pipeline."""

    def __init__(self, store: Any, primary: str) -> None:
        self._store = store
        self.primary = primary  # "qdrant" or "chroma", used in log messages

    @classmethod
    async def rag_vector_store_create(cls) -> "RagVectorStore":
        """Pick backend based on config: Qdrant if QDRANT_URL is set, ChromaDB otherwise."""
        settings = get_settings()
        embeddings = rag_embeddings_get_embeddings()

        if settings.qdrant_url:
            return await cls._rag_vector_store_create_qdrant(settings, embeddings)
        return cls._rag_vector_store_create_chroma(embeddings)

    @classmethod
    async def _rag_vector_store_create_qdrant(
        cls, settings: Any, embeddings: Any
    ) -> "RagVectorStore":
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )

        # Create collection on first deploy. INT8 quantization keeps RAM usage sane.
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION not in existing:
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
                quantization_config=ScalarQuantization(
                    scalar=ScalarQuantizationConfig(
                        type=ScalarType.INT8,
                        always_ram=True,
                    )
                ),
            )
            logger.info(RAG_LOG_VECTOR_STORE_CREATED_QDRANT.format(collection=COLLECTION))

        store = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION,
            embedding=embeddings,
        )
        logger.info(RAG_LOG_VECTOR_STORE_QDRANT_INIT)
        return cls(store, "qdrant")

    @classmethod
    def _rag_vector_store_create_chroma(cls, embeddings: Any) -> "RagVectorStore":
        client = chromadb.PersistentClient(
            path=RAG_VECTOR_STORE_CHROMA_PATH,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        store = Chroma(
            client=client,
            collection_name=COLLECTION,
            embedding_function=embeddings,
        )
        logger.info(RAG_LOG_VECTOR_STORE_CHROMA_INIT)
        return cls(store, "chroma")

    async def rag_vector_store_add_documents(self, docs: list) -> int:
        # Not every LangChain store implements the async variant yet
        if hasattr(self._store, "aadd_documents"):
            await self._store.aadd_documents(docs)
        else:
            self._store.add_documents(docs)
        return len(docs)

    def rag_vector_store_get_retriever(self, k: int = RAG_RETRIEVER_DEFAULT_K) -> Any:
        return self._store.as_retriever(search_kwargs={"k": k})
