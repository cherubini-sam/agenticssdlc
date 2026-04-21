"""Remote-write failure classification — silent failures become observable counters."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.core.core_remote_write import _record_remote_write_failure


class _Resp:
    """Minimal stand-in for httpx.Response."""

    def __init__(self, status: int) -> None:
        self.status_code = status


class TestRecordRemoteWriteFailure:
    """Tests for the failure-classification helper that feeds the Prometheus counter."""

    @pytest.mark.parametrize(
        "status_code, expected_status",
        [(401, "401"), (403, "403"), (429, "429"), (500, "500"), (503, "503")],
    )
    def test_http_status_error_records_http_label(
        self, status_code: int, expected_status: str
    ) -> None:
        recorder = MagicMock()
        exc = httpx.HTTPStatusError("boom", request=MagicMock(), response=_Resp(status_code))
        with patch(
            "src.api.middleware.api_middleware_observability.record_remote_write_failure",
            recorder,
        ):
            _record_remote_write_failure(exc)
        recorder.assert_called_once_with("http", expected_status)

    def test_timeout_classified_as_network_timeout(self) -> None:
        recorder = MagicMock()
        with patch(
            "src.api.middleware.api_middleware_observability.record_remote_write_failure",
            recorder,
        ):
            _record_remote_write_failure(httpx.ReadTimeout("slow"))
        recorder.assert_called_once_with("network", "timeout")

    def test_connect_error_classified_as_network_connect(self) -> None:
        recorder = MagicMock()
        with patch(
            "src.api.middleware.api_middleware_observability.record_remote_write_failure",
            recorder,
        ):
            _record_remote_write_failure(httpx.ConnectError("down"))
        recorder.assert_called_once_with("network", "connect")

    def test_unknown_exception_classified_as_unknown(self) -> None:
        recorder = MagicMock()
        with patch(
            "src.api.middleware.api_middleware_observability.record_remote_write_failure",
            recorder,
        ):
            _record_remote_write_failure(RuntimeError("weird"))
        recorder.assert_called_once_with("unknown", "unknown")

    def test_recorder_failure_is_swallowed(self) -> None:
        with patch(
            "src.api.middleware.api_middleware_observability.record_remote_write_failure",
            side_effect=Exception("counter broken"),
        ):
            _record_remote_write_failure(RuntimeError("x"))
