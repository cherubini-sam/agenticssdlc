"""LangChain-compatible wrapper around sentence-transformers for BGE embeddings."""

from __future__ import annotations

from functools import lru_cache

import torch
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from src.rag.rag_utils import RAG_EMBEDDINGS_BATCH_SIZE, RAG_EMBEDDINGS_MODEL_NAME


class RagEmbeddings(Embeddings):
    """Wraps sentence-transformers so LangChain vector stores can use BGE-large directly."""

    MODEL_NAME: str = RAG_EMBEDDINGS_MODEL_NAME

    def __init__(self) -> None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(self.MODEL_NAME, device=device)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # normalize_embeddings=True so we can use raw dot product as cosine sim
        return self.model.encode(
            texts, normalize_embeddings=True, batch_size=RAG_EMBEDDINGS_BATCH_SIZE
        ).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()


@lru_cache(maxsize=1)
def rag_embeddings_get_embeddings() -> RagEmbeddings:
    """Singleton: the model is cached for performance."""

    return RagEmbeddings()
