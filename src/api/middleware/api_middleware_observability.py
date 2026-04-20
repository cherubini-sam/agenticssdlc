"""Request timing + GCP-structured logging middleware, plus Prometheus metric helpers."""

from __future__ import annotations

import logging
import time
import uuid

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.agents.agents_utils import AGENTS_PROTOCOL_AGENT_NAME
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
    API_PROMETHEUS_WORKFLOWS_ACTIVE_DESC,
    API_PROMETHEUS_WORKFLOWS_ACTIVE_METRIC,
)
from src.core.core_config import core_config_get_settings as get_settings
from src.core.core_remote_write import schedule_remote_write, schedule_remote_write_gauge

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

_SKIP_PATHS: frozenset[str] = API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS


def record_metrics(
    agent: str,
    phase: str,
    status: str,
    latency_s: float,
    confidence: float | None = None,
) -> None:
    """Bump counters/histograms locally and optionally push to Grafana Cloud.

    Also fires a remote-write push to Grafana Cloud when the URL is configured
    in settings.

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

    settings = get_settings()
    if settings.grafana_prometheus_url:
        schedule_remote_write(
            agent=agent,
            phase=phase,
            status=status,
            latency_s=latency_s,
            confidence=confidence,
            url=settings.grafana_prometheus_url,
            instance_id=settings.grafana_instance_id,
            api_key=settings.grafana_api_key,
        )


def record_protocol_decision(status: str, gatekeeper_mode: str) -> None:
    """Increment protocol decision counter and optionally push to Grafana.

    Args:
        status: Protocol decision status (GREEN/ERROR).
        gatekeeper_mode: Evaluation mode used (llm or heuristic).
    """

    PROTOCOL_DECISIONS.labels(status=status, gatekeeper_mode=gatekeeper_mode).inc()
    settings = get_settings()
    if settings.grafana_prometheus_url:
        schedule_remote_write(
            agent=AGENTS_PROTOCOL_AGENT_NAME,
            phase="0",
            status=status,
            latency_s=0.0,
            url=settings.grafana_prometheus_url,
            instance_id=settings.grafana_instance_id,
            api_key=settings.grafana_api_key,
        )


def record_active_workflows(value: float) -> None:
    """Push the in-flight workflow gauge to both local registry and Grafana.

    Args:
        value: Current count of in-flight workflows to set on the gauge.
    """

    ACTIVE_WORKFLOWS.set(value)
    settings = get_settings()
    if settings.grafana_prometheus_url:
        schedule_remote_write_gauge(
            metric_name="agentics_sdlc_active_workflows",
            value=value,
            url=settings.grafana_prometheus_url,
            instance_id=settings.grafana_instance_id,
            api_key=settings.grafana_api_key,
        )


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
