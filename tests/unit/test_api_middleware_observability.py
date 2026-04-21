"""Regression tests: active-workflow mutations MUST hit the remote-write push path."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_adjust_active_workflows_pushes_post_mutation_value() -> None:
    """The helper must call ``record_active_workflows`` with the new count, not the old one."""

    from src.api.middleware import api_middleware_observability as obs

    with (
        patch.object(obs, "get_active_workflow_count", return_value=3),
        patch.object(obs, "record_active_workflows") as mock_record,
    ):
        result = obs.adjust_active_workflows(1)

    assert result == 4
    mock_record.assert_called_once_with(4)


def test_adjust_active_workflows_clamps_negative() -> None:
    """A stale decrement must not push a negative count to Grafana."""

    from src.api.middleware import api_middleware_observability as obs

    with (
        patch.object(obs, "get_active_workflow_count", return_value=0),
        patch.object(obs, "record_active_workflows") as mock_record,
    ):
        result = obs.adjust_active_workflows(-1)

    assert result == 0
    mock_record.assert_called_once_with(0)


def test_record_active_workflows_pushes_named_metric_to_grafana() -> None:
    """The gauge setter must fire ``schedule_remote_write_gauge`` with the dashboard metric name."""

    from src.api.middleware import api_middleware_observability as obs

    fake_settings = MagicMock(
        grafana_prometheus_url="https://prom.example/api/v1/write",
        grafana_instance_id="id-1",
        grafana_api_key="key-1",
    )
    with (
        patch.object(obs, "get_settings", return_value=fake_settings),
        patch.object(obs, "schedule_remote_write_gauge") as mock_push,
    ):
        obs.record_active_workflows(2)

    mock_push.assert_called_once()
    kwargs = mock_push.call_args.kwargs
    assert kwargs["metric_name"] == "agentics_sdlc_active_workflows"
    assert kwargs["value"] == 2


def test_record_remote_write_failure_increments_counter() -> None:
    """Failure classification labels the counter with kind + status."""

    from src.api.middleware import api_middleware_observability as obs

    labeled = MagicMock()
    with patch.object(obs.REMOTE_WRITE_FAILURES, "labels", return_value=labeled) as mock_labels:
        obs.record_remote_write_failure("http", "401")
        mock_labels.assert_called_with(kind="http", status="401")
    labeled.inc.assert_called_once()
