"""Async Supabase writer for agent_audit_log and workflow_snapshots."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from supabase import create_client

from src.analytics.analytics_utils import (
    ANALYTICS_ERR_SUPABASE_MISSING_CONFIG,
    ANALYTICS_ERR_SUPABASE_PING_FAILED,
    ANALYTICS_KEY_AGENT_NAME,
    ANALYTICS_KEY_CONFIDENCE,
    ANALYTICS_KEY_ERROR,
    ANALYTICS_KEY_FINAL_STATUS,
    ANALYTICS_KEY_LATENCY_MS,
    ANALYTICS_KEY_PHASE,
    ANALYTICS_KEY_PHASE_REACHED,
    ANALYTICS_KEY_RETRY_COUNT,
    ANALYTICS_KEY_SESSION_ID,
    ANALYTICS_KEY_SNAPSHOT_DATA,
    ANALYTICS_KEY_STATUS,
    ANALYTICS_KEY_TASK_CONTENT,
    ANALYTICS_LOG_SUPABASE_DISABLED,
    ANALYTICS_LOG_SUPABASE_INSERT_DEBUG,
    ANALYTICS_LOG_SUPABASE_INSERT_WARN,
    ANALYTICS_LOG_SUPABASE_UPSERT_DEBUG,
    ANALYTICS_LOG_SUPABASE_UPSERT_WARN,
    ANALYTICS_LOG_SUPABASE_VALIDATED,
    ANALYTICS_SUPABASE_FINAL_STATUS_COMPLETED,
    ANALYTICS_SUPABASE_FINAL_STATUS_FAILED,
    ANALYTICS_SUPABASE_FINAL_STATUS_RETRYING,
    ANALYTICS_SUPABASE_STATUS_ERROR,
    ANALYTICS_SUPABASE_STATUS_RETRY,
    ANALYTICS_SUPABASE_STATUS_SUCCESS,
    ANALYTICS_SUPABASE_TABLE_AUDIT,
    ANALYTICS_SUPABASE_TABLE_SNAPSHOT,
)
from src.core.core_config import core_config_get_settings as get_settings

logger = logging.getLogger(__name__)

# Module-level singleton so we only create one Supabase client per process
_supabase_client: Any | None = None


def _analytics_supabase_get_client(url: str, key: str) -> Any:
    """Lazy-init the module-level Supabase client singleton."""

    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialised for %s", url)
    return _supabase_client


class AnalyticsSupabaseIngest:
    """Non-blocking Supabase writer for agent telemetry.

    Writes to two tables (see platform/sql/init.sql):
      - agent_audit_log: one row per agent invocation
      - workflow_snapshots: one upserted row per session, updated each phase

    All writes run in a thread executor and swallow errors (logged, never raised).
    Silently disables itself when SUPABASE_URL/SUPABASE_KEY are missing.
    """

    _AUDIT_TABLE: str = ANALYTICS_SUPABASE_TABLE_AUDIT
    _SNAPSHOT_TABLE: str = ANALYTICS_SUPABASE_TABLE_SNAPSHOT

    _VALID_STATUS: frozenset[str] = frozenset(
        {
            ANALYTICS_SUPABASE_STATUS_SUCCESS,
            ANALYTICS_SUPABASE_STATUS_ERROR,
            ANALYTICS_SUPABASE_STATUS_RETRY,
        }
    )
    _VALID_FINAL_STATUS: frozenset[str] = frozenset(
        {
            ANALYTICS_SUPABASE_FINAL_STATUS_COMPLETED,
            ANALYTICS_SUPABASE_FINAL_STATUS_FAILED,
            ANALYTICS_SUPABASE_FINAL_STATUS_RETRYING,
        }
    )

    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.supabase_url
        self._key = settings.supabase_key
        self._enabled = bool(self._url and self._key)
        if not self._enabled:
            logger.info(ANALYTICS_LOG_SUPABASE_DISABLED)

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def _client(self) -> Any:
        return _analytics_supabase_get_client(self._url, self._key)

    async def analytics_supabase_validate_connection(self) -> bool:
        """Lightweight startup check: SELECT 1 row to verify credentials and table exist.
        Raises RuntimeError on failure so the app surfaces the problem at boot, not mid-request."""

        if not self._enabled:
            raise RuntimeError(ANALYTICS_ERR_SUPABASE_MISSING_CONFIG)
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._analytics_supabase_ping)
            logger.info(ANALYTICS_LOG_SUPABASE_VALIDATED.format(url=self._url))
            return True
        except Exception as exc:
            raise RuntimeError(
                ANALYTICS_ERR_SUPABASE_PING_FAILED.format(url=self._url, error=exc)
            ) from exc

    def _analytics_supabase_ping(self) -> None:
        self._client.table(self._AUDIT_TABLE).select("session_id").limit(1).execute()

    def _analytics_supabase_insert(self, table: str, row: dict[str, Any]) -> None:
        self._client.table(table).insert(row).execute()

    def _analytics_supabase_upsert(self, table: str, row: dict[str, Any]) -> None:
        self._client.table(table).upsert(row).execute()

    async def analytics_supabase_log_agent_call(
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
        """Insert one row into agent_audit_log. Non-blocking, errors are swallowed."""

        if not self._enabled:
            return

        row: dict[str, Any] = {
            ANALYTICS_KEY_SESSION_ID: session_id,
            ANALYTICS_KEY_AGENT_NAME: agent_name,
            ANALYTICS_KEY_PHASE: max(1, min(6, phase)),  # clamp to CHECK constraint range
            ANALYTICS_KEY_LATENCY_MS: round(latency_ms, 2),
            ANALYTICS_KEY_CONFIDENCE: round(min(max(confidence, 0.0), 1.0), 4),
            ANALYTICS_KEY_STATUS: (
                status if status in self._VALID_STATUS else ANALYTICS_SUPABASE_STATUS_ERROR
            ),
            ANALYTICS_KEY_TASK_CONTENT: task_content[:1024],
            ANALYTICS_KEY_ERROR: error or "",
        }

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, self._analytics_supabase_insert, self._AUDIT_TABLE, row
            )
            logger.debug(ANALYTICS_LOG_SUPABASE_INSERT_DEBUG.format(session=session_id))
        except Exception as exc:
            logger.warning(ANALYTICS_LOG_SUPABASE_INSERT_WARN.format(error=exc))

    async def analytics_supabase_upsert_workflow_snapshot(
        self,
        session_id: str,
        phase_reached: int,
        retry_count: int,
        final_status: str,
        confidence: float | None = None,
        latency_ms: float | None = None,
        snapshot_data: dict[str, Any] | None = None,
    ) -> None:
        """Upsert into workflow_snapshots (ON CONFLICT session_id).
        Non-blocking, errors swallowed.
        """

        if not self._enabled:
            return

        row: dict[str, Any] = {
            ANALYTICS_KEY_SESSION_ID: session_id,
            ANALYTICS_KEY_PHASE_REACHED: phase_reached,
            ANALYTICS_KEY_RETRY_COUNT: retry_count,
            ANALYTICS_KEY_FINAL_STATUS: (
                final_status
                if final_status in self._VALID_FINAL_STATUS
                else ANALYTICS_SUPABASE_FINAL_STATUS_FAILED
            ),
        }
        if confidence is not None:
            row[ANALYTICS_KEY_CONFIDENCE] = round(min(max(confidence, 0.0), 1.0), 4)
        if latency_ms is not None:
            row[ANALYTICS_KEY_LATENCY_MS] = round(latency_ms, 2)
        if snapshot_data is not None:
            row[ANALYTICS_KEY_SNAPSHOT_DATA] = snapshot_data

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, self._analytics_supabase_upsert, self._SNAPSHOT_TABLE, row
            )
            logger.debug(ANALYTICS_LOG_SUPABASE_UPSERT_DEBUG.format(session=session_id))
        except Exception as exc:
            logger.warning(ANALYTICS_LOG_SUPABASE_UPSERT_WARN.format(error=exc))

    # Convenience aliases
    log_agent_call = analytics_supabase_log_agent_call
    upsert_workflow_snapshot = analytics_supabase_upsert_workflow_snapshot


SupabaseIngest = AnalyticsSupabaseIngest
