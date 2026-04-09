"""core_logging local vs Cloud Run paths, log levels, and noisy logger suppression."""

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest

from core.core_logging import core_logging_setup_logging


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """Snapshot the root-logger state before each test and restore it afterwards."""

    root = logging.getLogger()
    original_level = root.level
    original_handlers = root.handlers[:]
    yield
    root.handlers = original_handlers
    root.setLevel(original_level)


class TestCoreLoggingSetupLogging:
    """Tests for core_logging_setup_logging local and Cloud Run paths."""

    def test_local_path_no_k_service(self) -> None:
        """Without K_SERVICE, root logger is set to INFO with at least one handler."""

        env = {k: v for k, v in os.environ.items() if k != "K_SERVICE"}
        with patch.dict(os.environ, env, clear=True):
            core_logging_setup_logging("INFO")

        root = logging.getLogger()
        assert root.level == logging.INFO
        assert len(root.handlers) >= 1

    def test_local_path_uses_stream_handler(self) -> None:
        """Local path installs a StreamHandler on the root logger."""

        env = {k: v for k, v in os.environ.items() if k != "K_SERVICE"}
        with patch.dict(os.environ, env, clear=True):
            core_logging_setup_logging("DEBUG")

        root = logging.getLogger()
        assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)

    def test_cloud_run_path_with_k_service_set(self) -> None:
        """K_SERVICE triggers the Cloud Run path and respects the requested log level."""

        with patch.dict(os.environ, {"K_SERVICE": "agentics-sdlc-api"}):
            core_logging_setup_logging("WARNING")

        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_custom_log_level_debug(self) -> None:
        """DEBUG level is applied to the root logger on the local path."""

        env = {k: v for k, v in os.environ.items() if k != "K_SERVICE"}
        with patch.dict(os.environ, env, clear=True):
            core_logging_setup_logging("DEBUG")

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_custom_log_level_error(self) -> None:
        """ERROR level is applied to the root logger on the local path."""

        env = {k: v for k, v in os.environ.items() if k != "K_SERVICE"}
        with patch.dict(os.environ, env, clear=True):
            core_logging_setup_logging("ERROR")

        root = logging.getLogger()
        assert root.level == logging.ERROR

    def test_noisy_loggers_suppressed(self) -> None:
        """httpx and chromadb loggers are clamped to WARNING even when root is DEBUG."""

        env = {k: v for k, v in os.environ.items() if k != "K_SERVICE"}
        with patch.dict(os.environ, env, clear=True):
            core_logging_setup_logging("DEBUG")

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("chromadb").level == logging.WARNING

    def test_json_formatter_used_in_cloud_run(self) -> None:
        """Cloud Run path installs a JSON formatter that produces brace-delimited output."""

        with patch.dict(os.environ, {"K_SERVICE": "test-service"}):
            core_logging_setup_logging("INFO")

        root = logging.getLogger()
        assert len(root.handlers) >= 1
        handler = root.handlers[0]
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        formatted = handler.formatter.format(record)
        assert "{" in formatted and "}" in formatted
