"""Shared constants for the storage layer."""

from __future__ import annotations

# Object path template — artifacts/{task_id}/{phase_with_ext}
STORAGE_GCS_OBJECT_PATH_TEMPLATE: str = "artifacts/{task_id}/{phase}"

# GCS URI prefix
STORAGE_GCS_URI_PREFIX: str = "gs://"

# Phase labels (include file extension)
STORAGE_GCS_PHASE_RESULT: str = "phase_5_result.md"
STORAGE_GCS_PHASE_VERDICT: str = "phase_6_verdict.json"

# Content types
STORAGE_GCS_CONTENT_TYPE_JSON: str = "application/json"
STORAGE_GCS_CONTENT_TYPE_MD: str = "text/markdown"

# Log templates
STORAGE_LOG_GCS_INIT: str = "StorageGcs initialised for bucket: {bucket}"
STORAGE_LOG_GCS_UPLOAD_OK: str = "Artifact uploaded to {uri}"
STORAGE_LOG_GCS_UPLOAD_WARN: str = "GCS artifact upload failed (non-fatal): {error}"
STORAGE_LOG_GCS_DISABLED: str = "GCS bucket not configured — artifact persistence disabled"
