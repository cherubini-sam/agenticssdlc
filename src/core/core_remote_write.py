"""Prometheus remote-write client for pushing metrics to Grafana Cloud."""

from __future__ import annotations

import asyncio
import logging
import struct
import time

import snappy

from src.core.core_utils import (
    CORE_REMOTE_WRITE_CONTENT_TYPE,
    CORE_REMOTE_WRITE_FAILURE_KIND_HTTP,
    CORE_REMOTE_WRITE_FAILURE_KIND_NETWORK,
    CORE_REMOTE_WRITE_FAILURE_KIND_UNKNOWN,
    CORE_REMOTE_WRITE_FAILURE_STATUS_CONNECT,
    CORE_REMOTE_WRITE_FAILURE_STATUS_TIMEOUT,
    CORE_REMOTE_WRITE_FAILURE_STATUS_UNKNOWN,
    CORE_REMOTE_WRITE_LOG_ERROR,
    CORE_REMOTE_WRITE_TIMEOUT_S,
)

logger = logging.getLogger(__name__)


def _record_remote_write_failure(exc: BaseException) -> None:
    """Classify ``exc`` and increment the ``remote_write_failures_total`` counter.

    Classification:
        - ``httpx.HTTPStatusError``  -> ``kind=http``,    ``status=<HTTP code>``.
        - ``httpx.TimeoutException`` -> ``kind=network``, ``status=timeout``.
        - ``httpx.ConnectError``     -> ``kind=network``, ``status=connect``.
        - other ``httpx.RequestError`` -> ``kind=network``, ``status=unknown``.
        - everything else            -> ``kind=unknown``, ``status=unknown``.

    Import of ``record_remote_write_failure`` is deferred to avoid a circular import with
    ``api_middleware_observability`` at module load time.
    """

    try:
        import httpx

        from src.api.middleware.api_middleware_observability import record_remote_write_failure

        if isinstance(exc, httpx.HTTPStatusError):
            record_remote_write_failure(
                CORE_REMOTE_WRITE_FAILURE_KIND_HTTP, str(exc.response.status_code)
            )
        elif isinstance(exc, httpx.TimeoutException):
            record_remote_write_failure(
                CORE_REMOTE_WRITE_FAILURE_KIND_NETWORK, CORE_REMOTE_WRITE_FAILURE_STATUS_TIMEOUT
            )
        elif isinstance(exc, httpx.ConnectError):
            record_remote_write_failure(
                CORE_REMOTE_WRITE_FAILURE_KIND_NETWORK, CORE_REMOTE_WRITE_FAILURE_STATUS_CONNECT
            )
        elif isinstance(exc, httpx.RequestError):
            record_remote_write_failure(
                CORE_REMOTE_WRITE_FAILURE_KIND_NETWORK, CORE_REMOTE_WRITE_FAILURE_STATUS_UNKNOWN
            )
        else:
            record_remote_write_failure(
                CORE_REMOTE_WRITE_FAILURE_KIND_UNKNOWN, CORE_REMOTE_WRITE_FAILURE_STATUS_UNKNOWN
            )
    except Exception:
        # Counter bookkeeping must never mask the original push failure.
        pass


# Hand-rolled protobuf encoder for the Prometheus remote-write wire format.
# Only covers WriteRequest -> TimeSeries -> Label + Sample — nothing else needed.


def _varint(value: int) -> bytes:
    """Protobuf varint encoding (unsigned).

    Args:
        value: Unsigned integer to encode.

    Returns:
        Protobuf varint bytes.
    """
    buf = []
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            buf.append(0x80 | bits)
        else:
            buf.append(bits)
            break
    return bytes(buf)


def _field_string(field_num: int, text: str) -> bytes:
    """Encode a UTF-8 string as a protobuf length-delimited field.

    Args:
        field_num: Protobuf field number.
        text: UTF-8 string value.

    Returns:
        Encoded length-delimited field bytes.
    """
    encoded = text.encode()
    return _varint((field_num << 3) | 2) + _varint(len(encoded)) + encoded


def _field_double(field_num: int, value: float) -> bytes:
    """Encode a 64-bit float as a protobuf fixed64 field.

    Args:
        field_num: Protobuf field number.
        value: 64-bit float.

    Returns:
        Encoded 64-bit field bytes.
    """
    return _varint((field_num << 3) | 1) + struct.pack("<d", value)


def _field_int64(field_num: int, value: int) -> bytes:
    """Encode an integer as a protobuf varint field.

    Args:
        field_num: Protobuf field number.
        value: Integer to encode.

    Returns:
        Encoded varint field bytes.
    """
    return _varint((field_num << 3) | 0) + _varint(value)


def _field_message(field_num: int, data: bytes) -> bytes:
    """Encode pre-serialized nested message bytes as a protobuf length-delimited field.

    Args:
        field_num: Protobuf field number.
        data: Pre-encoded nested message bytes.

    Returns:
        Encoded length-delimited message field bytes.
    """
    return _varint((field_num << 3) | 2) + _varint(len(data)) + data


def _build_write_request(metrics: list[dict]) -> bytes:
    """Serialize a list of metric dicts into a Prometheus WriteRequest protobuf.

    Args:
        metrics: List of dicts each with labels (dict mapping str to str,
            must include __name__), value (float), and ts_ms (int millisecond
            timestamp).

    Returns:
        Serialized WriteRequest protobuf bytes ready for snappy compression.
    """
    write_request = b""
    for m in metrics:
        ts_body = b""
        # Labels must be sorted per Prometheus convention
        for k, v in sorted(m["labels"].items()):
            label = _field_string(1, k) + _field_string(2, v)
            ts_body += _field_message(1, label)

        sample = _field_double(1, m["value"]) + _field_int64(2, m["ts_ms"])
        ts_body += _field_message(2, sample)

        write_request += _field_message(1, ts_body)

    return write_request


async def remote_write_push(
    agent: str,
    phase: str,
    status: str,
    latency_s: float,
    confidence: float | None,
    url: str,
    instance_id: str,
    api_key: str,
) -> None:
    """Fire-and-forget push of per-task metrics to Grafana Cloud.

    Cloud Run kills in-process counters on cold start, so we push
    immediately after every task to avoid losing data.

    Args:
        agent: Agent name label.
        phase: Workflow phase label.
        status: Call outcome label.
        latency_s: Latency in seconds.
        confidence: Optional confidence score. None skips the metric.
        url: Grafana remote-write endpoint URL.
        instance_id: Grafana Prometheus instance ID.
        api_key: Grafana API key for Basic Auth.
    """
    try:
        import httpx  # lazy import — keeps the module testable without httpx installed

        ts_ms = int(time.time() * 1000)
        base_labels = {"agent_name": agent, "phase": phase, "job": "agentics-sdlc-api"}

        metrics: list[dict] = [
            {
                "labels": {
                    "__name__": "agentics_sdlc_agent_calls_total",
                    "status": status,
                    **base_labels,
                },
                "value": 1.0,
                "ts_ms": ts_ms,
            },
            {
                "labels": {
                    "__name__": "agentics_sdlc_agent_latency_seconds",
                    **base_labels,
                },
                "value": latency_s,
                "ts_ms": ts_ms,
            },
        ]

        if confidence is not None:
            metrics.append(
                {
                    "labels": {
                        "__name__": "agentics_sdlc_agent_confidence",
                        "agent_name": agent,
                        "job": "agentics-sdlc-api",
                    },
                    "value": confidence,
                    "ts_ms": ts_ms,
                }
            )

        proto_bytes = _build_write_request(metrics)
        compressed = snappy.compress(proto_bytes)

        async with httpx.AsyncClient(timeout=CORE_REMOTE_WRITE_TIMEOUT_S) as client:
            resp = await client.post(
                url,
                content=compressed,
                headers={
                    "Content-Type": CORE_REMOTE_WRITE_CONTENT_TYPE,
                    "Content-Encoding": "snappy",
                    "X-Prometheus-Remote-Write-Version": "0.1.0",
                },
                auth=(instance_id, api_key),
            )
            resp.raise_for_status()

    except Exception as exc:
        _record_remote_write_failure(exc)
        logger.warning(CORE_REMOTE_WRITE_LOG_ERROR, exc)


def schedule_remote_write(
    agent: str,
    phase: str,
    status: str,
    latency_s: float,
    confidence: float | None,
    url: str,
    instance_id: str,
    api_key: str,
) -> None:
    """Drop a remote-write push onto the current event loop. No-ops if there isn't one.

    Args:
        agent: Agent name label.
        phase: Workflow phase label.
        status: Call outcome label.
        latency_s: Latency in seconds.
        confidence: Optional confidence score. None skips the metric.
        url: Grafana remote-write endpoint URL.
        instance_id: Grafana Prometheus instance ID.
        api_key: Grafana API key for Basic Auth.
    """

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            remote_write_push(
                agent, phase, status, latency_s, confidence, url, instance_id, api_key
            )
        )
    except RuntimeError:
        pass  # no event loop running (tests, sync callers)


async def _remote_write_gauge(
    metric_name: str, value: float, url: str, instance_id: str, api_key: str
) -> None:
    """Push a single gauge sample. Same fire-and-forget pattern as the main push."""

    try:
        import httpx

        ts_ms = int(time.time() * 1000)
        proto_bytes = _build_write_request(
            [
                {
                    "labels": {"__name__": metric_name, "job": "agentics-sdlc-api"},
                    "value": value,
                    "ts_ms": ts_ms,
                }
            ]
        )
        compressed = snappy.compress(proto_bytes)
        async with httpx.AsyncClient(timeout=CORE_REMOTE_WRITE_TIMEOUT_S) as client:
            resp = await client.post(
                url,
                content=compressed,
                headers={
                    "Content-Type": CORE_REMOTE_WRITE_CONTENT_TYPE,
                    "Content-Encoding": "snappy",
                    "X-Prometheus-Remote-Write-Version": "0.1.0",
                },
                auth=(instance_id, api_key),
            )
            resp.raise_for_status()
    except Exception as exc:
        _record_remote_write_failure(exc)
        logger.warning(CORE_REMOTE_WRITE_LOG_ERROR, exc)


def schedule_remote_write_gauge(
    metric_name: str, value: float, url: str, instance_id: str, api_key: str
) -> None:
    """Fire-and-forget gauge push onto the running event loop.

    Args:
        metric_name: Prometheus metric name (must include __name__).
        value: Gauge value to set.
        url: Grafana remote-write endpoint URL.
        instance_id: Grafana Prometheus instance ID.
        api_key: Grafana API key for Basic Auth.
    """

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_remote_write_gauge(metric_name, value, url, instance_id, api_key))
    except RuntimeError:
        pass
