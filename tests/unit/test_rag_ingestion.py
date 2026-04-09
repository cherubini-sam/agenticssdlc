"""Unit tests for RAG ingestion pipeline: load, chunk, deduplicate, manifest."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

import src.rag.rag_ingestion as ing_module
from src.rag.rag_ingestion import (
    _load_manifest,
    _save_manifest,
    rag_ingestion_chunk_documents,
    rag_ingestion_deduplicate,
    rag_ingestion_ingest,
    rag_ingestion_load_knowledge_base,
    rag_ingestion_reset_manifest,
)
from src.rag.rag_utils import RAG_KEY_CHUNK_HASH, RAG_KEY_SOURCE


class TestRagIngestionLoad:
    """Tests for rag_ingestion_load_knowledge_base file loading behaviour."""

    def test_load_skips_empty_files(self, tmp_path: Path) -> None:
        """Files containing only whitespace are skipped; non-empty files are loaded."""

        (tmp_path / "protocols").mkdir()
        (tmp_path / "protocols" / "empty.md").write_text("   \n", encoding="utf-8")
        (tmp_path / "protocols" / "real.md").write_text("# Real content", encoding="utf-8")

        docs = rag_ingestion_load_knowledge_base(str(tmp_path))
        assert len(docs) == 1
        assert docs[0].page_content == "# Real content"

    def test_load_excludes_artifacts_dir(self, tmp_path: Path) -> None:
        """Files under the 'artifacts' directory must not be loaded."""

        (tmp_path / "artifacts").mkdir()
        (tmp_path / "artifacts" / "task.md").write_text("# Task", encoding="utf-8")
        (tmp_path / "artifacts" / "implementation_plan.md").write_text("# Plan", encoding="utf-8")
        (tmp_path / "roles").mkdir()
        (tmp_path / "roles" / "roles_engineer.md").write_text("# Engineer role", encoding="utf-8")

        docs = rag_ingestion_load_knowledge_base(str(tmp_path))
        sources = [Path(d.metadata[RAG_KEY_SOURCE]) for d in docs]
        assert all(
            p.parent.name != "artifacts" for p in sources
        ), "Artifact files must not be loaded into the knowledge base"
        assert len(docs) == 1

    def test_load_attaches_category_metadata(self, tmp_path: Path) -> None:
        """Known parent dirs map to the correct category tag."""

        for subdir in ("protocols", "roles", "rules"):
            (tmp_path / subdir).mkdir(exist_ok=True)
            (tmp_path / subdir / f"{subdir}_foo.md").write_text(f"# {subdir}", encoding="utf-8")

        docs = rag_ingestion_load_knowledge_base(str(tmp_path))
        categories = {d.metadata["category"] for d in docs}
        assert categories == {"protocol", "role", "rule"}

    def test_load_unknown_dir_uses_general(self, tmp_path: Path) -> None:
        """Directories not in CATEGORY_MAP fall back to 'general'."""

        (tmp_path / "unknown").mkdir()
        (tmp_path / "unknown" / "file.md").write_text("content", encoding="utf-8")

        docs = rag_ingestion_load_knowledge_base(str(tmp_path))
        assert docs[0].metadata["category"] == "general"


class TestRagIngestionChunk:
    """Tests for rag_ingestion_chunk_documents splitting and metadata."""

    def test_chunk_attaches_hash(self) -> None:
        """Every chunk produced by the splitter must have a chunk_hash in metadata."""

        doc = Document(
            page_content="word " * 500,
            metadata={"category": "test", "filename": "test.md", "source": "test.md"},
        )

        chunks = rag_ingestion_chunk_documents([doc])
        assert len(chunks) > 1, "Expected multiple chunks from long document"
        for chunk in chunks:
            assert RAG_KEY_CHUNK_HASH in chunk.metadata
            assert len(chunk.metadata[RAG_KEY_CHUNK_HASH]) == 64

    def test_chunk_inherits_parent_metadata(self) -> None:
        """Chunks must carry forward all metadata fields from the parent document."""

        doc = Document(
            page_content="# Section\n\n" + "text " * 100,
            metadata={"category": "protocol", "filename": "proto.md", "source": "x/proto.md"},
        )

        chunks = rag_ingestion_chunk_documents([doc])
        for chunk in chunks:
            assert chunk.metadata["category"] == "protocol"
            assert chunk.metadata["filename"] == "proto.md"


class TestRagIngestionDeduplicate:
    """Tests for rag_ingestion_deduplicate hash-based deduplication."""

    def test_deduplicate_removes_duplicate_hashes(self) -> None:
        """Chunks with the same hash must appear only once in the output."""

        shared_hash = "a" * 64
        doc_a = Document(page_content="same", metadata={RAG_KEY_CHUNK_HASH: shared_hash})
        doc_b = Document(page_content="same", metadata={RAG_KEY_CHUNK_HASH: shared_hash})
        doc_c = Document(page_content="different", metadata={RAG_KEY_CHUNK_HASH: "b" * 64})

        result = rag_ingestion_deduplicate([doc_a, doc_b, doc_c])
        assert len(result) == 2

    def test_deduplicate_passes_through_hashless_chunks(self) -> None:
        """Chunks without a hash are included as-is without raising."""

        doc = Document(page_content="no hash", metadata={})

        result = rag_ingestion_deduplicate([doc])
        assert len(result) == 1


class TestRagIngestionManifest:
    """Tests for manifest load, save, and reset helpers."""

    def test_load_manifest_missing_returns_empty_set(self, tmp_path: Path) -> None:
        """Loading a non-existent manifest returns an empty set."""

        result = _load_manifest(str(tmp_path / "nonexistent.json"))
        assert result == set()

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Hashes saved to manifest are recovered identically on load."""

        hashes = {"aaa", "bbb", "ccc"}
        path = str(tmp_path / "manifest.json")
        _save_manifest(hashes, path)
        loaded = _load_manifest(path)
        assert loaded == hashes

    def test_reset_manifest_deletes_file(self, tmp_path: Path) -> None:
        """Resetting the manifest removes the file from disk."""

        manifest = tmp_path / "manifest.json"
        manifest.write_text("[]", encoding="utf-8")
        rag_ingestion_reset_manifest(str(manifest))
        assert not manifest.exists()


class TestRagIngestionIngest:
    """Tests for the top-level rag_ingestion_ingest pipeline."""

    @pytest.mark.asyncio
    async def test_ingest_skips_already_ingested_chunks(self, tmp_path: Path) -> None:
        """Chunks whose hash is already in the manifest must not be re-embedded."""

        (tmp_path / "roles").mkdir()
        (tmp_path / "roles" / "role.md").write_text("# Role\n\nContent here.", encoding="utf-8")

        docs = rag_ingestion_load_knowledge_base(str(tmp_path))
        chunks = rag_ingestion_chunk_documents(docs)
        all_hashes = {c.metadata[RAG_KEY_CHUNK_HASH] for c in chunks}

        mock_store = MagicMock()
        mock_store.primary = "chroma"
        mock_store.rag_vector_store_add_documents = AsyncMock(return_value=0)

        with (
            patch.object(ing_module, "_load_manifest", return_value=all_hashes),
            patch.object(ing_module, "_save_manifest"),
        ):
            count = await rag_ingestion_ingest(mock_store, str(tmp_path))

        assert count == 0
        mock_store.rag_vector_store_add_documents.assert_not_called()
