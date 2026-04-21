"""Regression tests: event-path remote-write is OFF — the heartbeat is the single writer.

``record_metrics``, ``record_protocol_decision``, and ``record_active_workflows``
must update the local Prometheus registry but must NOT schedule any remote-write
push. The heartbeat task in ``core_remote_write_heartbeat`` owns that path.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestApiMiddlewareObservabilityAdjustActiveWorkflows:
    """The ``adjust_active_workflows`` helper mutates the gauge locally only."""

    def test_adjust_active_workflows_pushes_post_mutation_value(self) -> None:
        from src.api.middleware import api_middleware_observability as obs

        with (
            patch.object(obs, "get_active_workflow_count", return_value=3),
            patch.object(obs, "record_active_workflows") as mock_record,
        ):
            result = obs.adjust_active_workflows(1)

        assert result == 4
        mock_record.assert_called_once_with(4)

    def test_adjust_active_workflows_clamps_negative(self) -> None:
        from src.api.middleware import api_middleware_observability as obs

        with (
            patch.object(obs, "get_active_workflow_count", return_value=0),
            patch.object(obs, "record_active_workflows") as mock_record,
        ):
            result = obs.adjust_active_workflows(-1)

        assert result == 0
        mock_record.assert_called_once_with(0)


class TestApiMiddlewareObservabilitySingleWriter:
    """Event-path handlers must not call into the remote-write module."""

    def test_record_active_workflows_does_not_schedule_remote_write(self) -> None:
        from src.api.middleware import api_middleware_observability as obs

        with patch("src.core.core_remote_write.schedule_remote_write_gauge") as mock_push:
            obs.record_active_workflows(2)

        mock_push.assert_not_called()
        assert obs.ACTIVE_WORKFLOWS._value.get() == 2

    def test_record_metrics_does_not_schedule_remote_write(self) -> None:
        from src.api.middleware import api_middleware_observability as obs

        with patch("src.core.core_remote_write.schedule_remote_write") as mock_push:
            obs.record_metrics("AgentX", "1", "success", 0.05, confidence=0.9)

        mock_push.assert_not_called()

    def test_record_protocol_decision_does_not_schedule_remote_write(self) -> None:
        from src.api.middleware import api_middleware_observability as obs

        with patch("src.core.core_remote_write.schedule_remote_write") as mock_push:
            obs.record_protocol_decision("GREEN", "heuristic")

        mock_push.assert_not_called()


class TestApiMiddlewareObservabilityRemoteWriteFailures:
    """Failure counter classification labels stay intact."""

    def test_record_remote_write_failure_increments_counter(self) -> None:
        from src.api.middleware import api_middleware_observability as obs

        labeled = MagicMock()
        with patch.object(obs.REMOTE_WRITE_FAILURES, "labels", return_value=labeled) as mock_labels:
            obs.record_remote_write_failure("http", "401")
            mock_labels.assert_called_with(kind="http", status="401")
        labeled.inc.assert_called_once()
