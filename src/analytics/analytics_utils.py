"""Shared constants for the analytics/telemetry layer."""

from __future__ import annotations

# BigQuery

ANALYTICS_BIGQUERY_TABLE_ID: str = "agent_audit_log"
ANALYTICS_BIGQUERY_TASK_CONTENT_MAX_LEN: int = 1024

ANALYTICS_BIGQUERY_DATASET_ID: str = "agentics_sdlc_analytics"

# Common dictionary keys (shared across BQ and Supabase)

ANALYTICS_KEY_TIMESTAMP: str = "timestamp"
ANALYTICS_KEY_TASK_ID: str = "task_id"
ANALYTICS_KEY_SENDER: str = "sender"
ANALYTICS_KEY_ROLE: str = "role"
ANALYTICS_KEY_CONTENT: str = "content"
ANALYTICS_KEY_METADATA: str = "metadata"
ANALYTICS_KEY_LATENCY: str = "latency"
ANALYTICS_KEY_SUCCESS: str = "success"

ANALYTICS_KEY_SESSION_ID: str = "session_id"
ANALYTICS_KEY_AGENT_NAME: str = "agent_name"
ANALYTICS_KEY_PHASE: str = "phase"
ANALYTICS_KEY_LATENCY_MS: str = "latency_ms"
ANALYTICS_KEY_CONFIDENCE: str = "confidence"
ANALYTICS_KEY_STATUS: str = "status"
ANALYTICS_KEY_TASK_CONTENT: str = "task_content"
ANALYTICS_KEY_ERROR: str = "error"
ANALYTICS_KEY_PHASE_REACHED: str = "phase_reached"
ANALYTICS_KEY_RETRY_COUNT: str = "retry_count"
ANALYTICS_KEY_FINAL_STATUS: str = "final_status"
ANALYTICS_KEY_SNAPSHOT_DATA: str = "snapshot_data"

# BigQuery log templates

ANALYTICS_LOG_BQ_INIT: str = "Initializing BigQuery client for dataset: {dataset}"
ANALYTICS_LOG_BQ_VALIDATE: str = "Validating BigQuery table: {table}"
ANALYTICS_LOG_BQ_INSERT_ERROR: str = "BigQuery insert error: {error}"
ANALYTICS_LOG_BQ_SCHEMA_ERROR: str = "BigQuery schema validation critical error: {error}"

# Supabase tables and status labels

ANALYTICS_SUPABASE_TABLE_AUDIT: str = "agent_audit_log"
ANALYTICS_SUPABASE_TABLE_SNAPSHOT: str = "workflow_snapshots"

ANALYTICS_SUPABASE_STATUS_SUCCESS: str = "success"
ANALYTICS_SUPABASE_STATUS_ERROR: str = "error"
ANALYTICS_SUPABASE_STATUS_RETRY: str = "retry"
ANALYTICS_SUPABASE_FINAL_STATUS_COMPLETED: str = "completed"
ANALYTICS_SUPABASE_FINAL_STATUS_FAILED: str = "failed"
ANALYTICS_SUPABASE_FINAL_STATUS_RETRYING: str = "retrying"

# Supabase log templates

ANALYTICS_LOG_SUPABASE_INIT: str = "Supabase client initialised for {url}"
ANALYTICS_LOG_SUPABASE_DISABLED: str = "Supabase URL/key not configured — Supabase logging disabled"
ANALYTICS_LOG_SUPABASE_VALIDATED: str = "Supabase connection validated ({url})"
ANALYTICS_LOG_SUPABASE_INSERT_DEBUG: str = "Supabase agent_audit_log inserted for session {session}"
ANALYTICS_LOG_SUPABASE_INSERT_WARN: str = (
    "Supabase agent_audit_log insert failed (non-fatal): {error}"
)
ANALYTICS_LOG_SUPABASE_UPSERT_DEBUG: str = (
    "Supabase workflow_snapshots upserted for session {session}"
)
ANALYTICS_LOG_SUPABASE_UPSERT_WARN: str = (
    "Supabase workflow_snapshots upsert failed (non-fatal): {error}"
)

# Supabase error messages

ANALYTICS_ERR_SUPABASE_MISSING_CONFIG: str = (
    "Supabase credentials (SUPABASE_URL / SUPABASE_KEY) are not configured."
)
ANALYTICS_ERR_SUPABASE_PING_FAILED: str = (
    "Supabase connection check failed for '{url}'. "
    "Verify credentials and network access. Original error: {error}"
)
