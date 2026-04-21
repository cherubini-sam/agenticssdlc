"""Centralized constants for the API layer."""

from __future__ import annotations

# Auth middleware

API_HEADER_API_KEY: str = "X-API-Key"
API_MIDDLEWARE_AUTH_MISSING_KEY_DETAIL: str = "X-API-Key header is required"
API_MIDDLEWARE_AUTH_MISSING_KEY_HINT: str = "Add header: X-API-Key: <your-key>"
API_MIDDLEWARE_AUTH_INVALID_KEY_DETAIL: str = "Invalid API key"
API_MIDDLEWARE_AUTH_BASIC_REALM: str = 'Basic realm="metrics"'
API_MIDDLEWARE_AUTH_UNAUTHORIZED: str = "Unauthorized"
API_MIDDLEWARE_AUTH_FORBIDDEN: str = "Forbidden"
API_MIDDLEWARE_AUTH_LOG_DISABLED: str = "Auth disabled: AGENTICS_SDLC_API_KEY not set"
API_MIDDLEWARE_AUTH_LOG_UNAUTHENTICATED: str = "Unauthenticated request: %s %s"
API_MIDDLEWARE_AUTH_LOG_INVALID_KEY: str = "Invalid API key attempt: %s %s key_prefix=%s..."
API_MIDDLEWARE_AUTH_LOG_INVALID_BASIC: str = "Invalid Basic Auth attempt on /metrics"

# No key required for these: health probes, docs, OpenAPI spec
API_MIDDLEWARE_AUTH_OPEN_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/readiness",
        "/liveness",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)

# Grafana scrape jobs authenticate via Basic Auth, not API key
API_MIDDLEWARE_AUTH_METRICS_PATHS: frozenset[str] = frozenset({"/metrics", "/metrics/"})

# Rate limit middleware

# Ops endpoints bypass the limiter so monitoring never gets throttled
API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/readiness",
        "/liveness",
        "/metrics",
        "/metrics/",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)

API_MIDDLEWARE_RATELIMIT_WINDOW: float = 60.0
API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM: int = 60

# Application metadata

API_APP_TITLE: str = "Agentics SDLC API"
API_APP_DESCRIPTION: str = "Production-grade multi-agent AI platform"
API_APP_VERSION: str = "1.0.0"

# CORS

API_CORS_ALLOW_METHODS: list[str] = ["GET", "POST"]
API_CORS_ALLOW_HEADERS: list[str] = ["X-API-Key", "Content-Type", "Authorization"]

# Routing

API_METRICS_MOUNT_PATH: str = "/metrics"
API_GCP_PROJECT_DEV_SENTINEL: str = "agentics-sdlc-dev"
API_SERVICE_NAME: str = "agentics-sdlc-api"
API_SERVICE_VERSION: str = API_APP_VERSION

# Agent status labels

API_AGENT_STATUS_ACTIVE: str = "active"
API_AGENT_STATUS_IDLE: str = "idle"
API_AGENT_LIBRARIAN_MODEL: str = "retrieval-only"

# Rate limit headers & error codes

API_RATELIMIT_HEADER_RETRY_AFTER: str = "Retry-After"
API_RATELIMIT_HEADER_LIMIT: str = "X-RateLimit-Limit"
API_RATELIMIT_HEADER_REMAINING: str = "X-RateLimit-Remaining"
API_RATELIMIT_HEADER_RESET: str = "X-RateLimit-Reset"
API_RATELIMIT_CLIENT_UNKNOWN: str = "unknown"
API_RATELIMIT_DETAIL_EXCEEDED: str = "Rate limit exceeded"
API_RATELIMIT_LOG_EXCEEDED: str = "Rate limit exceeded: client=%s path=%s"
API_RATELIMIT_EXCEEDED_ERROR_CODE: str = "RATE_001"
API_RATELIMIT_EXPOSE_HEADERS: list[str] = [
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "Retry-After",
]

# Prometheus metric definitions

API_PROMETHEUS_AGENT_CALLS_METRIC: str = "agentics_sdlc_agent_calls_total"
API_PROMETHEUS_AGENT_CALLS_DESC: str = "Agent invocation count"
API_PROMETHEUS_AGENT_CALLS_LABELS: list[str] = ["agent_name", "phase", "status"]

API_PROMETHEUS_AGENT_LATENCY_METRIC: str = "agentics_sdlc_agent_latency_seconds"
API_PROMETHEUS_AGENT_LATENCY_DESC: str = "Agent response time"
API_PROMETHEUS_AGENT_LATENCY_LABELS: list[str] = ["agent_name", "phase"]
API_PROMETHEUS_AGENT_LATENCY_BUCKETS: list[float] = [0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60]

API_PROMETHEUS_AGENT_CONFIDENCE_METRIC: str = "agentics_sdlc_agent_confidence"
API_PROMETHEUS_AGENT_CONFIDENCE_DESC: str = "Last confidence score per agent"
API_PROMETHEUS_AGENT_CONFIDENCE_LABELS: list[str] = ["agent_name"]

API_PROMETHEUS_WORKFLOWS_ACTIVE_METRIC: str = "agentics_sdlc_active_workflows"
API_PROMETHEUS_WORKFLOWS_ACTIVE_DESC: str = "In-flight LangGraph workflow count"

# Remote-write failure counter — exposed so silent push failures become visible on the dashboard.
API_PROMETHEUS_REMOTE_WRITE_FAILURES_METRIC: str = "agentics_sdlc_remote_write_failures_total"
API_PROMETHEUS_REMOTE_WRITE_FAILURES_DESC: str = (
    "Grafana remote-write push failures classified by kind and HTTP status"
)
API_PROMETHEUS_REMOTE_WRITE_FAILURES_LABELS: list[str] = ["kind", "status"]

# Active-workflow gauge delta constants — used by the router to signal enter/exit.
API_ROUTERS_TASKS_GAUGE_DELTA_INC: int = 1
API_ROUTERS_TASKS_GAUGE_DELTA_DEC: int = -1

# Protocol Decision Counter
API_PROMETHEUS_PROTOCOL_DECISIONS_METRIC: str = "agentics_sdlc_protocol_decisions_total"
API_PROMETHEUS_PROTOCOL_DECISIONS_DESC: str = "Protocol gatekeeper decisions by status and mode"
API_PROMETHEUS_PROTOCOL_DECISIONS_LABELS: list[str] = ["status", "gatekeeper_mode"]

# Observability middleware

# Skip these to keep structured logs clean (they'd just be noise)
API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS: frozenset[str] = frozenset(
    {"/metrics", "/health", "/readiness", "/liveness"}
)

# Observability middleware
API_OBSERVABILITY_LOG_REQUEST_ID: str = "requestId"
API_OBSERVABILITY_HEADER_REQUEST_ID: str = "X-Request-ID"

# GCP-structured log field names
API_OBSERVABILITY_LOG_HTTP_REQUEST: str = "httpRequest"
API_OBSERVABILITY_LOG_METHOD: str = "requestMethod"
API_OBSERVABILITY_LOG_URL: str = "requestUrl"
API_OBSERVABILITY_LOG_STATUS: str = "status"
API_OBSERVABILITY_LOG_LATENCY: str = "latency"
API_OBSERVABILITY_LOG_USER_AGENT: str = "userAgent"
API_HEADER_USER_AGENT: str = "user-agent"

# Main application logs

API_WARNINGS_LANGCHAIN_IGNORE: str = r"As of langchain-core"
API_MAIN_LOG_BQ_START: str = "BigQuery — validate schema and register audit logger"
API_MAIN_LOG_BQ_ERROR: str = "BigQuery schema validation failed (non-fatal): {error}"
API_MAIN_LOG_SUPABASE_START: str = "Supabase — validate connection and register audit logger"
API_MAIN_LOG_SUPABASE_ERROR: str = "Supabase connection check failed (non-fatal): {error}"
API_MAIN_STATUS_ENABLED: str = "enabled"
API_MAIN_STATUS_DISABLED: str = "disabled (local dev)"
API_MAIN_LOG_READY: str = "Ready — model: {model}, vector: {vector}, auth: {auth}"
API_MAIN_LOG_SHUTDOWN: str = "Shutdown complete"

# Router: Tasks

API_ROUTERS_TASKS_INTERNAL_ERROR: str = "An internal error occurred. Please try again."
API_ROUTERS_TASKS_LOG_AUDIT_FAILED: str = "Audit log failed for task %s: %s"
API_ROUTERS_TASKS_LOG_FAILED: str = "Task {task_id} failed: {error}"
API_ROUTERS_TASKS_STATUS_COMPLETED: str = "completed"
API_ROUTERS_TASKS_STATUS_FAILED: str = "failed"
API_ROUTERS_TASKS_NOT_FOUND: str = (
    "Task {task_id} not found. Agentics SDLC is stateless — results are returned synchronously."
)

# Router: Agents

API_ROUTERS_AGENTS_MANAGER: str = "MANAGER"
API_ROUTERS_AGENTS_ARCHITECT: str = "ARCHITECT"
API_ROUTERS_AGENTS_ENGINEER: str = "ENGINEER"
API_ROUTERS_AGENTS_VALIDATOR: str = "VALIDATOR"
API_ROUTERS_AGENTS_LIBRARIAN: str = "LIBRARIAN"
API_ROUTERS_AGENTS_REFLECTOR: str = "REFLECTOR"
API_ROUTERS_AGENTS_STATUS_SUCCESS: str = "success"
API_ROUTERS_AGENTS_STATUS_ERROR: str = "error"

# HTTP status codes used across the API

API_HTTP_200_OK: int = 200
API_HTTP_401_UNAUTHORIZED: int = 401
API_HTTP_403_FORBIDDEN: int = 403
API_HTTP_413_REQUEST_TOO_LARGE: int = 413
API_HTTP_429_TOO_MANY_REQUESTS: int = 429
API_HTTP_501_NOT_IMPLEMENTED: int = 501
API_HTTP_503_SERVICE_UNAVAILABLE: int = 503

# Latency unit conversion

API_MS_PER_SECOND: float = 1000.0

# Schema: task request validation

API_SCHEMAS_TASK_CONTENT_MAX_LENGTH: int = 4096
API_SCHEMAS_TASK_CONTENT_CONTROL_CHAR_PATTERN: str = r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
API_SCHEMAS_TASK_CONTENT_BLANK_ERROR: str = "content cannot be blank"
API_SCHEMAS_TASK_CONTEXT_MAX_BYTES: int = 8192
API_SCHEMAS_TASK_CONTEXT_TOO_LARGE_ERROR: str = "context payload exceeds 8 KB limit"

# Request body size limit

API_MAIN_MAX_REQUEST_BODY_BYTES: int = 65_536  # 64 KB
API_MAIN_REQUEST_BODY_TOO_LARGE: str = "Request body too large"
API_MAIN_LOG_CORS_WILDCARD: str = (
    "CORS: wildcard origin configured — allow_credentials is disabled. "
    "Set explicit origins to enable credentialed requests."
)

# Router: Health

API_HEALTH_STATUS_HEALTHY: str = "healthy"
API_HEALTH_STATUS_READY: str = "ready"
API_HEALTH_STATUS_NOT_READY: str = "not_ready"
API_HEALTH_STATUS_ALIVE: str = "alive"
API_HEALTH_KEY_STATUS: str = "status"
API_HEALTH_KEY_SERVICE: str = "service"
API_HEALTH_KEY_VERSION: str = "version"
API_HEALTH_KEY_CHECKS: str = "checks"
API_HEALTH_KEY_TIMESTAMP: str = "timestamp"
API_HEALTH_VAL_OK: str = "ok"
API_HEALTH_VAL_NOT_INIT: str = "not_initialized"
