"""Single-writer Grafana Cloud heartbeat task.

Pushes the live-panel metrics (``active_workflows``, ``agent_confidence``,
``agent_calls_total``, ``protocol_decisions_total``) at a fixed cadence from
the in-process Prometheus registry. Event-path code updates the registry
locally; this loop is the only caller that forwards to Grafana Cloud, which
avoids timestamp collisions and out-of-order rejects.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import time

from src.core.core_remote_write import _remote_write_send
from src.core.core_utils import (
    CORE_HEARTBEAT_LOG_START,
    CORE_HEARTBEAT_LOG_STOP,
    CORE_HEARTBEAT_LOG_TICK_ERROR,
    CORE_HEARTBEAT_METRIC_ACTIVE_WORKFLOWS,
    CORE_HEARTBEAT_METRIC_AGENT_CALLS_TOTAL,
    CORE_HEARTBEAT_METRIC_AGENT_CONFIDENCE,
    CORE_HEARTBEAT_METRIC_PROTOCOL_DECISIONS_TOTAL,
    CORE_REMOTE_WRITE_INSTANCE_ENV,
    CORE_REMOTE_WRITE_JOB_LABEL,
)

logger = logging.getLogger(__name__)


def core_heartbeat_resolve_instance() -> str:
    """Return the instance label for pushed series.

    Prefers the Cloud Run revision name when present (stable per-revision
    identity), falling back to the machine hostname for local dev.

    Returns:
        The resolved instance identifier string.
    """

    revision = os.environ.get(CORE_REMOTE_WRITE_INSTANCE_ENV)
    if revision:
        return revision
    return socket.gethostname()


def _collect_gauge_samples(
    metric: object, metric_name: str, base_labels: dict[str, str], ts_ms: int
) -> list[dict]:
    """Read current values from a ``prometheus_client`` Gauge (labelled or not).

    Args:
        metric: The Gauge singleton.
        metric_name: Prometheus metric name to emit under ``__name__``.
        base_labels: Labels merged into every sample (``job``, ``instance``).
        ts_ms: Timestamp (millisecond epoch) to stamp every sample with.

    Returns:
        List of sample dicts ready for ``_remote_write_send``.
    """

    samples: list[dict] = []
    label_names = getattr(metric, "_labelnames", ()) or ()
    children = getattr(metric, "_metrics", {}) or {}

    if label_names:
        # Labelled metric: iterate children (may be empty if no observations yet).
        for label_values, child in children.items():
            value = float(child._value.get())
            labels: dict[str, str] = {"__name__": metric_name, **base_labels}
            for name, value_str in zip(label_names, label_values):
                labels[name] = str(value_str)
            samples.append({"labels": labels, "value": value, "ts_ms": ts_ms})
        return samples

    # Unlabelled metric: value lives directly on the metric object.
    value = float(metric._value.get())  # type: ignore[attr-defined]
    labels = {"__name__": metric_name, **base_labels}
    samples.append({"labels": labels, "value": value, "ts_ms": ts_ms})
    return samples


def _collect_counter_samples(
    metric: object, metric_name: str, base_labels: dict[str, str], ts_ms: int
) -> list[dict]:
    """Read cumulative values from a ``prometheus_client`` Counter.

    Args:
        metric: The Counter singleton.
        metric_name: Prometheus metric name to emit under ``__name__``.
        base_labels: Labels merged into every sample (``job``, ``instance``).
        ts_ms: Timestamp (millisecond epoch) to stamp every sample with.

    Returns:
        List of cumulative sample dicts for every label combination observed
        so far. Empty when the counter has never been incremented.
    """

    samples: list[dict] = []
    label_names = getattr(metric, "_labelnames", ()) or ()
    children = getattr(metric, "_metrics", {}) or {}

    if label_names:
        # Labelled metric: iterate children (may be empty if counter never bumped).
        for label_values, child in children.items():
            value = float(child._value.get())
            labels: dict[str, str] = {"__name__": metric_name, **base_labels}
            for name, value_str in zip(label_names, label_values):
                labels[name] = str(value_str)
            samples.append({"labels": labels, "value": value, "ts_ms": ts_ms})
        return samples

    # Unlabelled counter: value lives directly on the metric object.
    value = float(metric._value.get())  # type: ignore[attr-defined]
    labels = {"__name__": metric_name, **base_labels}
    samples.append({"labels": labels, "value": value, "ts_ms": ts_ms})
    return samples


def core_heartbeat_collect(instance: str) -> list[dict]:
    """Snapshot the live-panel metrics from the in-process registry.

    Lazy-imports the Prometheus singletons from the middleware module to avoid
    an import cycle at module load time.

    Args:
        instance: Value for the ``instance`` label attached to every sample.

    Returns:
        List of sample dicts ready for ``_remote_write_send``. Covers the four
        metrics the Grafana dashboard live panels rely on.
    """

    from src.api.middleware.api_middleware_observability import (
        ACTIVE_WORKFLOWS,
        AGENT_CALLS,
        AGENT_CONFIDENCE,
        PROTOCOL_DECISIONS,
    )

    ts_ms = int(time.time() * 1000)
    base_labels: dict[str, str] = {
        "job": CORE_REMOTE_WRITE_JOB_LABEL,
        "instance": instance,
    }

    samples: list[dict] = []
    samples.extend(
        _collect_gauge_samples(
            ACTIVE_WORKFLOWS,
            CORE_HEARTBEAT_METRIC_ACTIVE_WORKFLOWS,
            base_labels,
            ts_ms,
        )
    )
    samples.extend(
        _collect_gauge_samples(
            AGENT_CONFIDENCE,
            CORE_HEARTBEAT_METRIC_AGENT_CONFIDENCE,
            base_labels,
            ts_ms,
        )
    )
    samples.extend(
        _collect_counter_samples(
            AGENT_CALLS,
            CORE_HEARTBEAT_METRIC_AGENT_CALLS_TOTAL,
            base_labels,
            ts_ms,
        )
    )
    samples.extend(
        _collect_counter_samples(
            PROTOCOL_DECISIONS,
            CORE_HEARTBEAT_METRIC_PROTOCOL_DECISIONS_TOTAL,
            base_labels,
            ts_ms,
        )
    )
    return samples


async def core_heartbeat_run(
    url: str,
    instance_id: str,
    api_key: str,
    interval_s: float,
    instance: str,
) -> None:
    """Run the heartbeat push loop until cancelled.

    First tick fires immediately so live panels populate at boot; subsequent
    ticks sleep ``interval_s`` between pushes. Per-tick exceptions are logged
    and swallowed so transient network failures never kill the loop.

    Args:
        url: Grafana remote-write endpoint URL.
        instance_id: Grafana Prometheus instance ID.
        api_key: Grafana API key for Basic Auth.
        interval_s: Seconds between heartbeat ticks.
        instance: Value for the ``instance`` label (per-revision identity).
    """

    logger.info(CORE_HEARTBEAT_LOG_START, interval_s, instance)
    try:
        while True:
            try:
                samples = core_heartbeat_collect(instance)
                if samples:
                    await _remote_write_send(samples, url, instance_id, api_key)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(CORE_HEARTBEAT_LOG_TICK_ERROR, exc)
            await asyncio.sleep(interval_s)
    except asyncio.CancelledError:
        logger.info(CORE_HEARTBEAT_LOG_STOP)
        raise
