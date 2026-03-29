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
from src.rag.rag_vector_store import RagVectorStore  # noqa: E402

logger = logging.getLogger(__name__)

_MSG_START: str = "Starting knowledge base ingestion..."
_MSG_COMPLETE: str = "Ingestion complete. Indexed %d document chunks."
_MSG_FAILED: str = "Ingestion failed: %s"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge base into vector store.")
    parser.add_argument("--path", default=".agent/", help="Path to scan for .md files")
    args = parser.parse_args()

    setup_logging()
    logger.info(_MSG_START)

    try:
        vector_store = await RagVectorStore.rag_vector_store_create()
        count = await ingest(vector_store, base_path=args.path)
        logger.info(_MSG_COMPLETE, count)
    except Exception as exc:
        logger.error(_MSG_FAILED, exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
