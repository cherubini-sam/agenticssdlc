"""Prometheus remote-write client for pushing metrics to Grafana Cloud."""

from __future__ import annotations

import asyncio
import logging
import struct
import time

import snappy

from src.core.core_utils import (
    CORE_REMOTE_WRITE_CONTENT_TYPE,
    CORE_REMOTE_WRITE_LOG_ERROR,
    CORE_REMOTE_WRITE_TIMEOUT_S,
)

logger = logging.getLogger(__name__)


# Hand-rolled protobuf encoder for the Prometheus remote-write wire format.
# Only covers WriteRequest -> TimeSeries -> Label + Sample — nothing else needed.


def _varint(value: int) -> bytes:
    """Protobuf varint encoding (unsigned)."""
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
    encoded = text.encode()
    return _varint((field_num << 3) | 2) + _varint(len(encoded)) + encoded


def _field_double(field_num: int, value: float) -> bytes:
    return _varint((field_num << 3) | 1) + struct.pack("<d", value)


def _field_int64(field_num: int, value: int) -> bytes:
    return _varint((field_num << 3) | 0) + _varint(value)


def _field_message(field_num: int, data: bytes) -> bytes:
    return _varint((field_num << 3) | 2) + _varint(len(data)) + data


def _build_write_request(metrics: list[dict]) -> bytes:
    """Serialize a list of metric dicts into a Prometheus WriteRequest protobuf.

    Each dict needs: labels (dict with __name__), value (float), ts_ms (int).
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
    """Drop a remote-write push onto the current event loop. No-ops if there isn't one."""

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
        logger.warning(CORE_REMOTE_WRITE_LOG_ERROR, exc)


def schedule_remote_write_gauge(
    metric_name: str, value: float, url: str, instance_id: str, api_key: str
) -> None:
    """Fire-and-forget gauge push onto the running event loop."""

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_remote_write_gauge(metric_name, value, url, instance_id, api_key))
    except RuntimeError:
        pass
