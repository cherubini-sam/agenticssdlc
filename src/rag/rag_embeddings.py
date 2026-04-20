"""LangChain-compatible wrapper around sentence-transformers for BGE embeddings."""

from __future__ import annotations

from functools import lru_cache

import torch
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from src.rag.rag_utils import RAG_EMBEDDINGS_BATCH_SIZE, RAG_EMBEDDINGS_MODEL_NAME


def rag_embeddings_detect_device() -> str:
    """Return the best available torch device: cuda > mps > cpu."""

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class RagEmbeddings(Embeddings):
    """Wraps sentence-transformers so LangChain vector stores can use BGE-large directly."""

    def __init__(self, model_name: str = RAG_EMBEDDINGS_MODEL_NAME) -> None:
        """
        Args:
            model_name: HuggingFace model identifier for SentenceTransformer;
                defaults to BAAI/bge-large-en-v1.5.
        """
        device = rag_embeddings_detect_device()
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents.

        Args:
            texts: List of document strings to embed.

        Returns:
            List of 1024-dim normalized float vectors, one per input text.
        """

        # normalize_embeddings=True so we can use raw dot product as cosine sim
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=RAG_EMBEDDINGS_BATCH_SIZE,
            show_progress_bar=False,
        ).tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a query.

        Args:
            text: Query string to embed.

        Returns:
            1024-dim normalized float vector.
        """

        return self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()


@lru_cache(maxsize=1)
def rag_embeddings_get_embeddings() -> RagEmbeddings:
    """Singleton: the model is cached for performance."""

    return RagEmbeddings()
