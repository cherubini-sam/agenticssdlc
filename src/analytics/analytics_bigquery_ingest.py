"""Async BigQuery writer for the agent_audit_log table."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from src.analytics.analytics_utils import (
    ANALYTICS_BIGQUERY_TABLE_ID,
    ANALYTICS_BIGQUERY_TASK_CONTENT_MAX_LEN,
    ANALYTICS_KEY_AGENT_NAME,
    ANALYTICS_KEY_CONFIDENCE,
    ANALYTICS_KEY_ERROR,
    ANALYTICS_KEY_LATENCY_MS,
    ANALYTICS_KEY_PHASE,
    ANALYTICS_KEY_SESSION_ID,
    ANALYTICS_KEY_STATUS,
    ANALYTICS_KEY_TASK_CONTENT,
    ANALYTICS_KEY_TIMESTAMP,
    ANALYTICS_LOG_BQ_INIT,
    ANALYTICS_LOG_BQ_INSERT_ERROR,
    ANALYTICS_LOG_BQ_SCHEMA_ERROR,
    ANALYTICS_LOG_BQ_VALIDATE,
)
from src.core.core_config import core_config_get_settings as get_settings

logger = logging.getLogger(__name__)

# One BQ client per container lifetime
_bq_client: Any | None = None


def _analytics_bigquery_get_bq_client(project_id: str) -> Any:
    """Lazy-init the module-level BigQuery client singleton.

    Args:
        project_id: GCP project ID for the BigQuery client.

    Returns:
        Singleton bigquery.Client instance.
    """

    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=project_id)
        logger.info(ANALYTICS_LOG_BQ_INIT.format(dataset=project_id))
    return _bq_client


class AnalyticsBigqueryIngest:
    """Non-blocking BigQuery writer for agent audit rows."""

    TABLE_ID: str = ANALYTICS_BIGQUERY_TABLE_ID

    def __init__(self) -> None:
        settings = get_settings()
        self._project = settings.gcp_project_id
        self._dataset = settings.bigquery_dataset
        self._full_table = f"{self._project}.{self._dataset}.{self.TABLE_ID}"

    @property
    def _client(self) -> Any:
        return _analytics_bigquery_get_bq_client(self._project)

    async def analytics_bigquery_validate_schema(self) -> bool:
        """Fail-fast startup check that the audit_log table exists in BQ."""

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._analytics_bigquery_check_table_exists)
            logger.info(ANALYTICS_LOG_BQ_VALIDATE.format(table=self._full_table))
            return True
        except Exception as exc:
            error_msg = ANALYTICS_LOG_BQ_SCHEMA_ERROR.format(error=str(exc))
            raise RuntimeError(error_msg) from exc

    def _analytics_bigquery_check_table_exists(self) -> None:
        self._client.get_table(self._full_table)

    def _analytics_bigquery_build_row(
        self,
        session_id: str,
        agent_name: str,
        phase: int,
        latency_ms: float,
        confidence: float,
        status: str,
        task_content: str = "",
        error: str | None = None,
    ) -> dict[str, Any]:
        """Assemble the row dict for a streaming insert.

        Args:
            session_id: Workflow run identifier.
            agent_name: Name of the agent that produced this row.
            phase: Workflow phase number (1–6).
            latency_ms: Elapsed time in milliseconds.
            confidence: Normalized confidence score (0–1).
            status: One of success/error/retry.
            task_content: Raw task string (truncated to max allowed length).
            error: Error message string or None.

        Returns:
            Dict formatted for BigQuery streaming insert with all required column keys.
        """

        return {
            ANALYTICS_KEY_SESSION_ID: session_id,
            ANALYTICS_KEY_AGENT_NAME: agent_name,
            ANALYTICS_KEY_PHASE: phase,
            ANALYTICS_KEY_LATENCY_MS: latency_ms,
            ANALYTICS_KEY_CONFIDENCE: confidence,
            ANALYTICS_KEY_STATUS: status,
            ANALYTICS_KEY_TASK_CONTENT: task_content[:ANALYTICS_BIGQUERY_TASK_CONTENT_MAX_LEN],
            ANALYTICS_KEY_ERROR: error or "",
            ANALYTICS_KEY_TIMESTAMP: datetime.now(timezone.utc).isoformat(),
        }

    async def analytics_bigquery_log_agent_call(
        self,
        session_id: str,
        agent_name: str,
        phase: int,
        latency_ms: float,
        confidence: float,
        status: str,
        task_content: str = "",
        error: str | None = None,
    ) -> None:
        """Non-blocking insert: errors are logged and never raised.

        Args:
            session_id: Workflow run identifier.
            agent_name: Name of the agent that produced this row.
            phase: Workflow phase number (1–6).
            latency_ms: Elapsed time in milliseconds.
            confidence: Normalized confidence score (0–1).
            status: One of success/error/retry.
            task_content: Raw task string (truncated to max allowed length).
            error: Error message string or None.
        """

        row = self._analytics_bigquery_build_row(
            session_id=session_id,
            agent_name=agent_name,
            phase=phase,
            latency_ms=latency_ms,
            confidence=confidence,
            status=status,
            task_content=task_content,
            error=error,
        )
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._analytics_bigquery_insert_row, row)
        except RuntimeError:
            # No running event loop; fall back to synchronous insert
            self._analytics_bigquery_insert_row(row)
        except Exception as exc:
            logger.warning("BigQuery insert failed (non-fatal): %s", exc)

    def _analytics_bigquery_insert_row(self, row: dict[str, Any]) -> None:
        """Synchronous streaming insert into BigQuery.

        Args:
            row: Dict formatted by _analytics_bigquery_build_row.
        """

        try:
            errors = self._client.insert_rows_json(
                self._full_table, [row], ignore_unknown_values=True
            )
            if errors:
                logger.error(ANALYTICS_LOG_BQ_INSERT_ERROR.format(error=str(errors)))
            else:
                logger.info(
                    "BigQuery audit row inserted successfully for session %s | table: %s",
                    row[ANALYTICS_KEY_SESSION_ID],
                    self._full_table,
                )
        except Exception as exc:
            logger.error(
                "BigQuery critical ingestion failure: %s | table: %s", exc, self._full_table
            )
