"""Knowledge base ingestion: load markdown, chunk, embed, store."""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.rag.rag_utils import (
    RAG_INGEST_MANIFEST_PATH,
    RAG_INGESTION_CATEGORY_MAP,
    RAG_INGESTION_CHUNK_OVERLAP,
    RAG_INGESTION_CHUNK_SIZE,
    RAG_INGESTION_EXCLUDED_DIRS,
    RAG_INGESTION_SEPARATORS,
    RAG_KEY_CATEGORY,
    RAG_KEY_CHUNK_HASH,
    RAG_KEY_FILENAME,
    RAG_KEY_SOURCE,
    RAG_LOG_INGESTION_CATEGORY_UNMAPPED,
    RAG_LOG_INGESTION_CHUNKED,
    RAG_LOG_INGESTION_COMPLETE,
    RAG_LOG_INGESTION_LOAD_ERROR,
    RAG_LOG_INGESTION_LOADED,
    RAG_LOG_INGESTION_SKIPPED,
    RAG_LOG_INGESTION_STATS,
    RAG_LOG_VECTOR_STORE_MANIFEST_DELETED,
    RAG_LOG_VECTOR_STORE_MANIFEST_READ_ERROR,
    RAG_LOG_VECTOR_STORE_NO_NEW_CHUNKS,
)

logger = logging.getLogger(__name__)

_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=RAG_INGESTION_CHUNK_SIZE,
    chunk_overlap=RAG_INGESTION_CHUNK_OVERLAP,
    separators=RAG_INGESTION_SEPARATORS,
)


def rag_ingestion_load_knowledge_base(base_path: str = ".agent/") -> list[Document]:
    """Walk base_path and load every .md file as a Document with category metadata."""

    docs: list[Document] = []
    base = Path(base_path)
    loaded = skipped = errors = 0

    for md_file in base.rglob("*.md"):
        if md_file.parent.name in RAG_INGESTION_EXCLUDED_DIRS:
            skipped += 1
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            if not content.strip():
                skipped += 1
                continue

            parent = md_file.parent.name
            if parent not in RAG_INGESTION_CATEGORY_MAP:
                logger.debug(RAG_LOG_INGESTION_CATEGORY_UNMAPPED, parent)
            category = RAG_INGESTION_CATEGORY_MAP.get(parent, "general")

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
            logger.warning(RAG_LOG_INGESTION_LOAD_ERROR, md_file, e)
            errors += 1

    logger.info(RAG_LOG_INGESTION_LOADED, loaded, base_path)
    logger.info(RAG_LOG_INGESTION_STATS, loaded, skipped, errors)
    return docs


def rag_ingestion_chunk_documents(docs: list[Document]) -> list[Document]:
    """Split into overlapping chunks. Metadata carries over from the parent doc."""

    chunks = _SPLITTER.split_documents(docs)

    for chunk in chunks:
        chunk.metadata[RAG_KEY_CHUNK_HASH] = hashlib.sha256(chunk.page_content.encode()).hexdigest()

    logger.info(RAG_LOG_INGESTION_CHUNKED, len(docs), len(chunks))
    return chunks


def rag_ingestion_deduplicate(chunks: list[Document]) -> list[Document]:
    """Remove duplicate chunks within a batch using their content hash."""

    seen: set[str] = set()
    unique: list[Document] = []
    for chunk in chunks:
        chunk_hash = chunk.metadata.get(RAG_KEY_CHUNK_HASH)
        if chunk_hash is None:
            unique.append(chunk)
            continue
        if chunk_hash not in seen:
            seen.add(chunk_hash)
            unique.append(chunk)
    return unique


def _load_manifest(path: str = RAG_INGEST_MANIFEST_PATH) -> set[str]:
    """Return the set of chunk hashes already persisted in the vector store."""

    manifest_file = Path(path)
    if not manifest_file.exists():
        return set()
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set()
    except Exception as e:
        logger.warning(RAG_LOG_VECTOR_STORE_MANIFEST_READ_ERROR, path, e)
        return set()


def _save_manifest(seen: set[str], path: str = RAG_INGEST_MANIFEST_PATH) -> None:
    """Persist the full set of ingested chunk hashes to the manifest file."""

    manifest_file = Path(path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")


def rag_ingestion_reset_manifest(path: str = RAG_INGEST_MANIFEST_PATH) -> None:
    """Delete the ingest manifest so the next run re-ingests everything.

    Call this after a vector store reset to keep the manifest in sync.
    """
    manifest_file = Path(path)
    if manifest_file.exists():
        manifest_file.unlink()
        logger.info(RAG_LOG_VECTOR_STORE_MANIFEST_DELETED, path)


async def rag_ingestion_ingest(vector_store: Any, base_path: str = ".agent/") -> int:
    """Run the full pipeline: load -> chunk -> deduplicate -> filter new -> embed+store."""

    docs = rag_ingestion_load_knowledge_base(base_path)
    loop = asyncio.get_running_loop()
    chunks = await loop.run_in_executor(
        None, functools.partial(rag_ingestion_chunk_documents, docs)
    )
    chunks = rag_ingestion_deduplicate(chunks)

    manifest = _load_manifest()
    new_chunks = [c for c in chunks if c.metadata.get(RAG_KEY_CHUNK_HASH) not in manifest]
    skipped_count = len(chunks) - len(new_chunks)
    if skipped_count:
        logger.info(RAG_LOG_INGESTION_SKIPPED, skipped_count)

    if not new_chunks:
        logger.info(RAG_LOG_VECTOR_STORE_NO_NEW_CHUNKS)
        return 0

    count = await vector_store.rag_vector_store_add_documents(new_chunks)

    new_hashes = {
        c.metadata[RAG_KEY_CHUNK_HASH] for c in new_chunks if RAG_KEY_CHUNK_HASH in c.metadata
    }
    _save_manifest(manifest | new_hashes)

    logger.info(RAG_LOG_INGESTION_COMPLETE, count, vector_store.primary)
    return count
