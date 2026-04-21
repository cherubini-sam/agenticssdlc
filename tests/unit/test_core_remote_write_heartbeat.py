"""Tests for the single-writer Grafana heartbeat task."""

from __future__ import annotations

import asyncio
import logging
import socket
from unittest.mock import AsyncMock, patch

import pytest

from src.core import core_remote_write_heartbeat as hb
from src.core.core_utils import (
    CORE_HEARTBEAT_LOG_STOP,
    CORE_HEARTBEAT_METRIC_ACTIVE_WORKFLOWS,
    CORE_HEARTBEAT_METRIC_AGENT_CALLS_TOTAL,
    CORE_HEARTBEAT_METRIC_AGENT_CONFIDENCE,
    CORE_REMOTE_WRITE_INSTANCE_ENV,
    CORE_REMOTE_WRITE_JOB_LABEL,
)


def _reset_metric(metric: object) -> None:
    """Clear any previously-seen label combinations on a prometheus_client metric."""

    children = getattr(metric, "_metrics", None)
    if children is not None:
        children.clear()
    value = getattr(metric, "_value", None)
    if value is not None and hasattr(value, "set"):
        value.set(0)


@pytest.fixture(autouse=True)
def _clean_metrics() -> None:
    """Ensure each test starts with a clean Prometheus registry state."""

    from src.api.middleware.api_middleware_observability import (
        ACTIVE_WORKFLOWS,
        AGENT_CALLS,
        AGENT_CONFIDENCE,
        PROTOCOL_DECISIONS,
    )

    for metric in (ACTIVE_WORKFLOWS, AGENT_CALLS, AGENT_CONFIDENCE, PROTOCOL_DECISIONS):
        _reset_metric(metric)


class TestCoreRemoteWriteHeartbeatResolveInstance:
    """Instance label derivation from env / hostname."""

    def test_prefers_k_revision_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CORE_REMOTE_WRITE_INSTANCE_ENV, "revision-007")
        assert hb.core_remote_write_heartbeat_resolve_instance() == "revision-007"

    def test_falls_back_to_hostname(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CORE_REMOTE_WRITE_INSTANCE_ENV, raising=False)
        assert hb.core_remote_write_heartbeat_resolve_instance() == socket.gethostname()


class TestCoreRemoteWriteHeartbeatCollect:
    """Reading cumulative / current values from the local Prometheus registry."""

    def test_counter_cumulative_value_and_labels(self) -> None:
        from src.api.middleware.api_middleware_observability import AGENT_CALLS

        AGENT_CALLS.labels(agent_name="X", phase="1", status="success").inc()
        AGENT_CALLS.labels(agent_name="X", phase="1", status="success").inc()
        AGENT_CALLS.labels(agent_name="X", phase="1", status="success").inc()

        samples = hb.core_remote_write_heartbeat_collect("inst-a")
        calls = [
            s for s in samples if s["labels"]["__name__"] == CORE_HEARTBEAT_METRIC_AGENT_CALLS_TOTAL
        ]
        assert len(calls) == 1
        sample = calls[0]
        assert sample["value"] == 3.0
        for key in ("agent_name", "phase", "status", "job", "instance"):
            assert key in sample["labels"]
        assert sample["labels"]["job"] == CORE_REMOTE_WRITE_JOB_LABEL
        assert sample["labels"]["instance"] == "inst-a"

    def test_gauge_unlabelled_active_workflows(self) -> None:
        from src.api.middleware.api_middleware_observability import ACTIVE_WORKFLOWS

        ACTIVE_WORKFLOWS.set(5)
        samples = hb.core_remote_write_heartbeat_collect("inst-a")
        gauges = [
            s for s in samples if s["labels"]["__name__"] == CORE_HEARTBEAT_METRIC_ACTIVE_WORKFLOWS
        ]
        assert len(gauges) == 1
        assert gauges[0]["value"] == 5.0
        assert gauges[0]["labels"]["instance"] == "inst-a"

    def test_labelled_gauge_agent_confidence(self) -> None:
        from src.api.middleware.api_middleware_observability import AGENT_CONFIDENCE

        AGENT_CONFIDENCE.labels(agent_name="A").set(0.91)
        AGENT_CONFIDENCE.labels(agent_name="B").set(0.42)

        samples = hb.core_remote_write_heartbeat_collect("inst-a")
        confs = [
            s for s in samples if s["labels"]["__name__"] == CORE_HEARTBEAT_METRIC_AGENT_CONFIDENCE
        ]
        assert len(confs) == 2
        by_name = {s["labels"]["agent_name"]: s["value"] for s in confs}
        assert by_name == {"A": 0.91, "B": 0.42}


class TestCoreRemoteWriteHeartbeatRunTick:
    """The run loop fires the first tick before sleeping."""

    @pytest.mark.asyncio
    async def test_first_tick_before_sleep_and_multiple_ticks(self) -> None:
        from src.api.middleware.api_middleware_observability import AGENT_CALLS

        AGENT_CALLS.labels(agent_name="X", phase="1", status="success").inc()

        spy = AsyncMock()
        sleep_calls: list[float] = []

        async def fake_sleep(delay: float) -> None:
            sleep_calls.append(delay)
            if len(sleep_calls) >= 2:
                raise asyncio.CancelledError()

        with (
            patch.object(hb, "_remote_write_send", spy),
            patch.object(hb.asyncio, "sleep", side_effect=fake_sleep),
        ):
            task = asyncio.create_task(
                hb.core_remote_write_heartbeat_run(
                    "https://example/push", "id", "key", 0.01, "inst-a"
                )
            )
            with pytest.raises(asyncio.CancelledError):
                await task

        assert spy.await_count >= 2
        assert sleep_calls  # slept at least once, meaning tick ran first


class TestCoreRemoteWriteHeartbeatCancel:
    """Cancelling the task logs the stop message and propagates CancelledError."""

    @pytest.mark.asyncio
    async def test_cancel_logs_stop(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger=hb.logger.name)

        spy = AsyncMock()
        with patch.object(hb, "_remote_write_send", spy):
            task = asyncio.create_task(
                hb.core_remote_write_heartbeat_run(
                    "https://example/push", "id", "key", 10.0, "inst-a"
                )
            )
            await asyncio.sleep(0)  # let the task enter the loop
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        assert CORE_HEARTBEAT_LOG_STOP in caplog.text


class TestCoreRemoteWriteHeartbeatTickError:
    """Per-tick transport failures never kill the loop."""

    @pytest.mark.asyncio
    async def test_exception_logged_and_loop_continues(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.WARNING, logger=hb.logger.name)

        attempts: dict[str, int] = {"count": 0}

        async def flaky_send(*args: object, **kwargs: object) -> None:
            attempts["count"] += 1
            raise RuntimeError("boom")

        sleep_calls: list[float] = []

        async def fake_sleep(delay: float) -> None:
            sleep_calls.append(delay)
            if attempts["count"] >= 2:
                raise asyncio.CancelledError()

        with (
            patch.object(hb, "_remote_write_send", flaky_send),
            patch.object(hb.asyncio, "sleep", side_effect=fake_sleep),
        ):
            task = asyncio.create_task(
                hb.core_remote_write_heartbeat_run(
                    "https://example/push", "id", "key", 0.01, "inst-a"
                )
            )
            with pytest.raises(asyncio.CancelledError):
                await task

        assert attempts["count"] >= 2
        assert "boom" in caplog.text
