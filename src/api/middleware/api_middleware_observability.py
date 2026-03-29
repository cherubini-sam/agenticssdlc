"""Request timing + GCP-structured logging middleware, plus Prometheus metric helpers."""

from __future__ import annotations

import logging
import time

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.api.api_utils import (
    API_HEADER_USER_AGENT,
    API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS,
    API_OBSERVABILITY_LOG_HTTP_REQUEST,
    API_OBSERVABILITY_LOG_LATENCY,
    API_OBSERVABILITY_LOG_METHOD,
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

_SKIP_PATHS: frozenset[str] = API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS


def record_metrics(
    agent: str,
    phase: str,
    status: str,
    latency_s: float,
    confidence: float | None = None,
) -> None:
    """Bump counters/histograms locally and optionally push to Grafana Cloud."""

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


def record_active_workflows(value: float) -> None:
    """Push the in-flight workflow gauge to both local registry and Grafana."""

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
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        latency = time.perf_counter() - start

        logger.info(
            API_OBSERVABILITY_LOG_HTTP_REQUEST,
            {
                API_OBSERVABILITY_LOG_METHOD: request.method,
                API_OBSERVABILITY_LOG_URL: str(request.url),
                API_OBSERVABILITY_LOG_STATUS: response.status_code,
                API_OBSERVABILITY_LOG_LATENCY: f"{latency:.3f}s",
                API_OBSERVABILITY_LOG_USER_AGENT: request.headers.get(API_HEADER_USER_AGENT, ""),
            },
        )

        return response
