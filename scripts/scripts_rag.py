"""CLI script to ingest knowledge base documents into the vector store."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from src.core.core_logging import core_logging_setup_logging as setup_logging  # noqa: E402
from src.rag.rag_ingestion import rag_ingestion_ingest as ingest  # noqa: E402
from src.rag.rag_vector_store import (  # noqa: E402
    RagVectorStore,
    rag_vector_store_reset_and_rebuild,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """CLI script to ingest knowledge base documents into the vector store."""

    parser = argparse.ArgumentParser(
        description="Ingest knowledge base into vector store.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path", default=".agent/rag/", help="Path to scan for .md files (default: .agent/rag/)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Wipe the vector store collection and ingest manifest before ingesting. "
            "Use this after structural changes to chunk parameters or knowledge-base layout."
        ),
    )
    args = parser.parse_args()

    setup_logging()

    try:
        if args.reset:
            logger.info("Starting full reset and rebuild of knowledge base...")
            count = await rag_vector_store_reset_and_rebuild(base_path=args.path)
        else:
            logger.info("Starting knowledge base ingestion...")
            vector_store = await RagVectorStore.rag_vector_store_create()
            count = await ingest(vector_store, base_path=args.path)

        logger.info("Ingestion complete. Indexed %d document chunks.", count)
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
