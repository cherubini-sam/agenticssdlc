"""Shared constants used across the core package."""

from __future__ import annotations

# Config defaults
CORE_CONFIG_ENV_FILE: str = ".env"
CORE_CONFIG_ENV_ENCODING: str = "utf-8"
CORE_CONFIG_DEFAULT_GCP_PROJECT: str = "agentics-sdlc-dev"
CORE_CONFIG_DEFAULT_GCP_REGION: str = "us-central1"
CORE_CONFIG_DEFAULT_GCS_BUCKET: str = "artifacts-agentics-sdlc-dev"
CORE_CONFIG_DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"
CORE_CONFIG_DEFAULT_BIGQUERY_DATASET: str = "agentics_sdlc_analytics"
CORE_CONFIG_DEFAULT_PORT: int = 8080
CORE_CONFIG_DEFAULT_RATE_LIMIT_RPM: int = 60
CORE_CONFIG_MISSING_PROJECT_ID_ERROR: str = "GCP_PROJECT_ID is required"

# LLM
CORE_LLM_DEFAULT_TEMPERATURE: float = 0.1

# Safety settings left as None to use Vertex AI defaults.
# Passing custom SafetySetting objects causes type conflicts between
# vertexai.generative_models and langchain-google-vertexai internals.
CORE_LLM_SAFETY_SETTINGS = None

# Logging
CORE_LOGGING_DEFAULT_LOG_LEVEL: str = "INFO"
CORE_LOGGING_K_SERVICE_ENV: str = "K_SERVICE"
CORE_LOGGING_JSON_TIMESTAMP_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%03dZ"
CORE_LOGGING_JSON_KEY_SEVERITY: str = "severity"
CORE_LOGGING_JSON_KEY_MESSAGE: str = "message"
CORE_LOGGING_JSON_KEY_LOGGER: str = "logger"
CORE_LOGGING_JSON_KEY_TIMESTAMP: str = "timestamp"
CORE_LOGGING_JSON_KEY_EXCEPTION: str = "exception"
CORE_LOGGING_CONSOLE_FORMAT: str = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
CORE_LOGGING_CONSOLE_DATE_FORMAT: str = "%H:%M:%S"

# Remote write
CORE_REMOTE_WRITE_TIMEOUT_S: float = 5.0
CORE_REMOTE_WRITE_LOG_ERROR: str = "Grafana remote-write failed (non-fatal): %s"
CORE_REMOTE_WRITE_CONTENT_TYPE: str = "application/x-protobuf"
CORE_REMOTE_WRITE_PROTO_VERSION: str = "0.1.0"

# Chatty third-party loggers we dial down to WARNING
CORE_LOGGING_NOISY_LOGGERS: list[str] = [
    "httpx",
    "httpcore",
    "urllib3",
    "google.auth",
    "chromadb",
    "sentence_transformers",
]
