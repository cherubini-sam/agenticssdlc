"""Request timing + GCP-structured logging middleware, plus Prometheus metric helpers."""

from __future__ import annotations

import logging
import time
import uuid

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.api.api_utils import (
    API_HEADER_USER_AGENT,
    API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS,
    API_OBSERVABILITY_HEADER_REQUEST_ID,
    API_OBSERVABILITY_LOG_HTTP_REQUEST,
    API_OBSERVABILITY_LOG_LATENCY,
    API_OBSERVABILITY_LOG_METHOD,
    API_OBSERVABILITY_LOG_REQUEST_ID,
    API_OBSERVABILITY_LOG_STATUS,
    API_OBSERVABILITY_LOG_URL,
    API_OBSERVABILITY_LOG_USER_AGENT,
    API_PROMETHEUS_AGENT_CALLS_DESC,
    API_PROMETHEUS_AGENT_CALLS_LABELS,
    API_PROMETHEUS_AGENT_CALLS_METRIC,
    API_PROMETHEUS_AGENT_CONFIDENCE_DESC,
    API_PROMETHEUS_AGENT_CONFIDENCE_LABELS,
    API_PROMETHEUS_AGENT_CONFIDENCE_METRIC,
    API_PROMETHEUS_AGENT_LATENCY_BUCKETS,
    API_PROMETHEUS_AGENT_LATENCY_DESC,
    API_PROMETHEUS_AGENT_LATENCY_LABELS,
    API_PROMETHEUS_AGENT_LATENCY_METRIC,
    API_PROMETHEUS_PROTOCOL_DECISIONS_DESC,
    API_PROMETHEUS_PROTOCOL_DECISIONS_LABELS,
    API_PROMETHEUS_PROTOCOL_DECISIONS_METRIC,
    API_PROMETHEUS_REMOTE_WRITE_FAILURES_DESC,
    API_PROMETHEUS_REMOTE_WRITE_FAILURES_LABELS,
    API_PROMETHEUS_REMOTE_WRITE_FAILURES_METRIC,
    API_PROMETHEUS_WORKFLOWS_ACTIVE_DESC,
    API_PROMETHEUS_WORKFLOWS_ACTIVE_METRIC,
)

logger = logging.getLogger(__name__)

# Prometheus singletons (registered once at import time)

AGENT_CALLS = Counter(
    API_PROMETHEUS_AGENT_CALLS_METRIC,
    API_PROMETHEUS_AGENT_CALLS_DESC,
    API_PROMETHEUS_AGENT_CALLS_LABELS,
)
AGENT_LATENCY = Histogram(
    API_PROMETHEUS_AGENT_LATENCY_METRIC,
    API_PROMETHEUS_AGENT_LATENCY_DESC,
    API_PROMETHEUS_AGENT_LATENCY_LABELS,
    buckets=API_PROMETHEUS_AGENT_LATENCY_BUCKETS,
)
AGENT_CONFIDENCE = Gauge(
    API_PROMETHEUS_AGENT_CONFIDENCE_METRIC,
    API_PROMETHEUS_AGENT_CONFIDENCE_DESC,
    API_PROMETHEUS_AGENT_CONFIDENCE_LABELS,
)
ACTIVE_WORKFLOWS = Gauge(
    API_PROMETHEUS_WORKFLOWS_ACTIVE_METRIC,
    API_PROMETHEUS_WORKFLOWS_ACTIVE_DESC,
)
PROTOCOL_DECISIONS = Counter(
    API_PROMETHEUS_PROTOCOL_DECISIONS_METRIC,
    API_PROMETHEUS_PROTOCOL_DECISIONS_DESC,
    API_PROMETHEUS_PROTOCOL_DECISIONS_LABELS,
)
REMOTE_WRITE_FAILURES = Counter(
    API_PROMETHEUS_REMOTE_WRITE_FAILURES_METRIC,
    API_PROMETHEUS_REMOTE_WRITE_FAILURES_DESC,
    API_PROMETHEUS_REMOTE_WRITE_FAILURES_LABELS,
)

_SKIP_PATHS: frozenset[str] = API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS


def record_metrics(
    agent: str,
    phase: str,
    status: str,
    latency_s: float,
    confidence: float | None = None,
) -> None:
    """Bump counters/histograms in the local Prometheus registry.

    Remote-write handled by core_remote_write_heartbeat (single-writer to avoid
    out-of-order rejects).

    Args:
        agent: Agent name string for label.
        phase: Workflow phase string.
        status: Call outcome (success/error/retry).
        latency_s: Elapsed time in seconds.
        confidence: Confidence score. None skips the gauge update.
    """

    AGENT_CALLS.labels(agent_name=agent, phase=phase, status=status).inc()
    AGENT_LATENCY.labels(agent_name=agent, phase=phase).observe(latency_s)
    if confidence is not None:
        AGENT_CONFIDENCE.labels(agent_name=agent).set(confidence)


def record_protocol_decision(status: str, gatekeeper_mode: str) -> None:
    """Increment the protocol decision counter in the local registry.

    Remote-write handled by core_remote_write_heartbeat (single-writer to avoid
    out-of-order rejects).

    Args:
        status: Protocol decision status (GREEN/ERROR).
        gatekeeper_mode: Evaluation mode used (llm or heuristic).
    """

    PROTOCOL_DECISIONS.labels(status=status, gatekeeper_mode=gatekeeper_mode).inc()


def record_remote_write_failure(kind: str, status: str) -> None:
    """Record a Grafana remote-write push failure so regressions are observable on the dashboard.

    Args:
        kind: Failure class (``http``, ``network``, ``unknown``).
        status: Specific status (HTTP code as string, ``timeout``, ``connect``, ``unknown``).
    """

    REMOTE_WRITE_FAILURES.labels(kind=kind, status=status).inc()


def record_active_workflows(value: float) -> None:
    """Set the in-flight workflow gauge in the local Prometheus registry.

    Remote-write handled by core_remote_write_heartbeat (single-writer to avoid
    out-of-order rejects).

    Args:
        value: Current count of in-flight workflows to set on the gauge.
    """

    ACTIVE_WORKFLOWS.set(value)


class ApiMiddlewareObservability(BaseHTTPMiddleware):
    """Emits a GCP-structured httpRequest log line for every non-infra request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Emit a GCP-structured log line and attach a request ID to the response.

        Args:
            request: Starlette request.
            call_next: Next handler.

        Returns:
            Response with X-Request-ID header added.
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        latency = time.perf_counter() - start

        response.headers[API_OBSERVABILITY_HEADER_REQUEST_ID] = request_id

        logger.info(
            API_OBSERVABILITY_LOG_HTTP_REQUEST,
            {
                API_OBSERVABILITY_LOG_METHOD: request.method,
                API_OBSERVABILITY_LOG_URL: str(request.url),
                API_OBSERVABILITY_LOG_STATUS: response.status_code,
                API_OBSERVABILITY_LOG_LATENCY: f"{latency:.3f}s",
                API_OBSERVABILITY_LOG_USER_AGENT: request.headers.get(API_HEADER_USER_AGENT, ""),
                API_OBSERVABILITY_LOG_REQUEST_ID: request_id,
            },
        )

        return response


def get_active_workflow_count() -> int:
    """Return the current number of in-flight workflows from the Prometheus gauge."""

    try:
        return int(ACTIVE_WORKFLOWS._value.get())
    except Exception:
        return 0


def adjust_active_workflows(delta: int) -> int:
    """Mutate the active-workflow gauge by ``delta`` and push the post-mutation value to Grafana.

    The router used to call ``ACTIVE_WORKFLOWS.inc()``/``.dec()`` directly, which updated the
    in-process gauge but never triggered a remote-write push — starving the dashboard.

    Args:
        delta: Signed integer increment (``+1`` on entry, ``-1`` on exit).

    Returns:
        The post-mutation active-workflow count (never negative).
    """

    current = get_active_workflow_count()
    next_value = max(0, current + int(delta))
    record_active_workflows(next_value)
    return next_value
