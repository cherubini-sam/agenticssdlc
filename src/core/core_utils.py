"""Shared constants used across the core package."""

from __future__ import annotations

# Config defaults
CORE_CONFIG_ENV_FILE: str = ".env"
CORE_CONFIG_ENV_ENCODING: str = "utf-8"
CORE_CONFIG_DEFAULT_GCP_PROJECT: str = "agentics-sdlc-dev"
CORE_CONFIG_DEFAULT_GCP_REGION: str = "us-central1"
CORE_CONFIG_DEFAULT_GCS_BUCKET: str = "artifacts-agentics-sdlc"
CORE_CONFIG_DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"
CORE_CONFIG_DEFAULT_BIGQUERY_DATASET: str = "agentics_sdlc_analytics"
CORE_CONFIG_DEFAULT_PORT: int = 8080
CORE_CONFIG_DEFAULT_RATE_LIMIT_RPM: int = 60
CORE_CONFIG_TUNED_PROTOCOL_ENDPOINT_ID_DEFAULT: str = ""
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
CORE_REMOTE_WRITE_JOB_LABEL: str = "agentics-sdlc-api"
CORE_REMOTE_WRITE_INSTANCE_ENV: str = "K_REVISION"

# Heartbeat (single-writer, Grafana Cloud live-panel push)
CORE_HEARTBEAT_INTERVAL_S: float = 10.0
CORE_HEARTBEAT_LOG_START: str = "Grafana heartbeat task started (interval=%.1fs, instance=%s)"
CORE_HEARTBEAT_LOG_STOP: str = "Grafana heartbeat task stopped"
CORE_HEARTBEAT_LOG_TICK_ERROR: str = "Grafana heartbeat tick failed: %s"
CORE_HEARTBEAT_LOG_PRECONDITION_MISSING: str = (
    "Grafana heartbeat NOT started - missing credential(s): %s"
)
CORE_HEARTBEAT_METRIC_ACTIVE_WORKFLOWS: str = "agentics_sdlc_active_workflows"
CORE_HEARTBEAT_METRIC_AGENT_CONFIDENCE: str = "agentics_sdlc_agent_confidence"
CORE_HEARTBEAT_METRIC_AGENT_CALLS_TOTAL: str = "agentics_sdlc_agent_calls_total"
CORE_HEARTBEAT_METRIC_PROTOCOL_DECISIONS_TOTAL: str = "agentics_sdlc_protocol_decisions_total"

# Failure classification labels used by record_remote_write_failure
CORE_REMOTE_WRITE_FAILURE_KIND_HTTP: str = "http"
CORE_REMOTE_WRITE_FAILURE_KIND_NETWORK: str = "network"
CORE_REMOTE_WRITE_FAILURE_KIND_UNKNOWN: str = "unknown"
CORE_REMOTE_WRITE_FAILURE_STATUS_TIMEOUT: str = "timeout"
CORE_REMOTE_WRITE_FAILURE_STATUS_CONNECT: str = "connect"
CORE_REMOTE_WRITE_FAILURE_STATUS_UNKNOWN: str = "unknown"

# Chatty third-party loggers we dial down to WARNING
CORE_LOGGING_NOISY_LOGGERS: list[str] = [
    "httpx",
    "httpcore",
    "urllib3",
    "google.auth",
    "chromadb",
    "sentence_transformers",
]
