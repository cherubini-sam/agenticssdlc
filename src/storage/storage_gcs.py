"""Async-compatible GCS writer for agent-generated artifacts."""

from __future__ import annotations

import json
import logging
from typing import Any

from google.cloud import storage

from src.core.core_config import core_config_get_settings as get_settings
from src.storage.storage_utils import (
    STORAGE_GCS_CONTENT_TYPE_JSON,
    STORAGE_GCS_CONTENT_TYPE_MD,
    STORAGE_GCS_OBJECT_PATH_TEMPLATE,
    STORAGE_GCS_URI_PREFIX,
    STORAGE_LOG_GCS_DISABLED,
    STORAGE_LOG_GCS_INIT,
    STORAGE_LOG_GCS_UPLOAD_OK,
    STORAGE_LOG_GCS_UPLOAD_WARN,
)

logger = logging.getLogger(__name__)

# One GCS client per container lifetime
_gcs_client: Any | None = None


def _storage_gcs_get_client() -> Any:
    """Lazy-init the module-level GCS client singleton."""

    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client()
    return _gcs_client


class StorageGcs:
    """Non-blocking GCS writer for artifact blobs."""

    def __init__(self) -> None:
        settings = get_settings()
        self._bucket_name = settings.gcs_bucket
        if self._bucket_name:
            logger.info(STORAGE_LOG_GCS_INIT.format(bucket=self._bucket_name))
        else:
            logger.warning(STORAGE_LOG_GCS_DISABLED)

    @property
    def is_enabled(self) -> bool:
        return bool(self._bucket_name)

    def storage_gcs_upload_artifact(self, task_id: str, phase: str, content: Any) -> str | None:
        """Upload an artifact dict/string to GCS and return its gs:// URI."""

        if not self.is_enabled:
            return None

        object_path = STORAGE_GCS_OBJECT_PATH_TEMPLATE.format(task_id=task_id, phase=phase)

        try:
            if phase.endswith(".md"):
                payload = content if isinstance(content, str) else str(content)
                content_type = STORAGE_GCS_CONTENT_TYPE_MD
            else:
                payload = (
                    content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
                )
                content_type = STORAGE_GCS_CONTENT_TYPE_JSON

            client = _storage_gcs_get_client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(object_path)
            blob.upload_from_string(payload, content_type=content_type)

            uri = f"{STORAGE_GCS_URI_PREFIX}{self._bucket_name}/{object_path}"
            logger.info(STORAGE_LOG_GCS_UPLOAD_OK.format(uri=uri))
            return uri

        except Exception as exc:
            logger.warning(STORAGE_LOG_GCS_UPLOAD_WARN.format(error=exc))
            return None
