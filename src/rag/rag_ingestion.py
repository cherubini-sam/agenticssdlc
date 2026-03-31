"""Knowledge base ingestion: load markdown, chunk, embed, store."""

from __future__ import annotations

import asyncio
import functools
import hashlib
import logging
from pathlib import Path
from typing import Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.rag.rag_utils import (
    RAG_INGESTION_CATEGORY_MAP,
    RAG_INGESTION_CHUNK_OVERLAP,
    RAG_INGESTION_CHUNK_SIZE,
    RAG_INGESTION_SEPARATORS,
    RAG_KEY_CATEGORY,
    RAG_KEY_CHUNK_HASH,
    RAG_KEY_FILENAME,
    RAG_KEY_SOURCE,
    RAG_LOG_INGESTION_CATEGORY_UNMAPPED,
    RAG_LOG_INGESTION_CHUNKED,
    RAG_LOG_INGESTION_COMPLETE,
    RAG_LOG_INGESTION_LOADED,
    RAG_LOG_INGESTION_STATS,
)

logger = logging.getLogger(__name__)

CHUNK_SIZE: int = RAG_INGESTION_CHUNK_SIZE
CHUNK_OVERLAP: int = RAG_INGESTION_CHUNK_OVERLAP
CATEGORY_MAP: dict[str, str] = RAG_INGESTION_CATEGORY_MAP


def rag_ingestion_load_knowledge_base(base_path: str = ".agent/") -> list[Document]:
    """Walk .agent/ and load every .md file as a Document with category metadata."""

    docs: list[Document] = []
    base = Path(base_path)
    loaded = skipped = errors = 0

    for md_file in base.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if not content.strip():
                skipped += 1
                continue

            # Parent dir name determines the category tag (e.g. "protocols" -> "protocol")
            parent = md_file.parent.name
            if parent not in CATEGORY_MAP:
                logger.debug(RAG_LOG_INGESTION_CATEGORY_UNMAPPED, parent)
            category = CATEGORY_MAP.get(parent, "general")

            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        RAG_KEY_CATEGORY: category,
                        RAG_KEY_FILENAME: md_file.name,
                        RAG_KEY_SOURCE: str(md_file),
                    },
                )
            )
            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load {md_file}: {e}")
            errors += 1

    logger.info(RAG_LOG_INGESTION_LOADED.format(count=loaded, path=base_path))
    logger.info(RAG_LOG_INGESTION_STATS.format(loaded=loaded, skipped=skipped, errors=errors))
    return docs


def rag_ingestion_chunk_documents(docs: list[Document]) -> list[Document]:
    """Split into overlapping chunks. Metadata carries over from the parent doc."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=RAG_INGESTION_SEPARATORS,
    )
    chunks = splitter.split_documents(docs)

    # Stamp each chunk with a content hash for deduplication
    for chunk in chunks:
        chunk.metadata[RAG_KEY_CHUNK_HASH] = hashlib.sha256(chunk.page_content.encode()).hexdigest()

    logger.info(RAG_LOG_INGESTION_CHUNKED.format(docs=len(docs), chunks=len(chunks)))
    return chunks


def rag_ingestion_deduplicate(chunks: list[Document]) -> list[Document]:
    """Remove duplicate chunks within a batch using their content hash."""

    seen: set[str] = set()
    unique: list[Document] = []
    for chunk in chunks:
        hash = chunk.metadata.get(RAG_KEY_CHUNK_HASH)
        if hash is None:
            # Hash missing (e.g. chunk created outside pipeline) — include as-is
            unique.append(chunk)
            continue
        if hash not in seen:
            seen.add(hash)
            unique.append(chunk)
    return unique


async def rag_ingestion_ingest(vector_store: Any, base_path: str = ".agent/") -> int:
    """Run the full pipeline: load -> chunk -> deduplicate -> embed+store."""

    docs = rag_ingestion_load_knowledge_base(base_path)
    # Chunking is CPU-bound; offload to a thread so we don't block the event loop
    loop = asyncio.get_event_loop()
    chunks = await loop.run_in_executor(
        None, functools.partial(rag_ingestion_chunk_documents, docs)
    )
    chunks = rag_ingestion_deduplicate(chunks)
    count = await vector_store.rag_vector_store_add_documents(chunks)
    logger.info(RAG_LOG_INGESTION_COMPLETE.format(count=count, store=vector_store.primary))
    return count
