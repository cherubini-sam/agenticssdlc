"""Hermetic unit tests for core_tracing.core_tracing_configure."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import core.core_tracing as core_tracing_mod
from core.core_config import CoreSettings
from core.core_tracing import (
    CORE_TRACING_HEADER,
    CORE_TRACING_LOG_ENABLED,
    CORE_TRACING_LOG_UNAVAILABLE,
    core_tracing_configure,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(
    *, tracing: bool = False, api_key: str = "", workspace: str = ""
) -> CoreSettings:
    """Build a CoreSettings with explicit tracing and workspace values."""
    s = CoreSettings()
    s.langchain_tracing_v2 = tracing
    s.langchain_api_key = api_key
    s.langchain_workspace_id = workspace
    return s


class _FakeSession:
    """Minimal requests.Session stub."""

    def __init__(self) -> None:
        self.headers: dict[str, str] = {}


class _FakeClient:
    """Minimal langsmith.Client stub."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.session = _FakeSession()


def _make_fake_langsmith(client_cls: type) -> types.ModuleType:
    """Build a fake 'langsmith' module with a given Client class."""
    mod = types.ModuleType("langsmith")
    mod.Client = client_cls  # type: ignore[attr-defined]
    return mod


@pytest.fixture(autouse=True)
def _reset_patch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset the _PATCHED sentinel and any injected fake langsmith before each test."""
    monkeypatch.setattr(core_tracing_mod, "_PATCHED", False)
    # Remove fake langsmith from sys.modules so each test gets a clean slate.
    sys.modules.pop("langsmith", None)
    yield
    monkeypatch.setattr(core_tracing_mod, "_PATCHED", False)
    sys.modules.pop("langsmith", None)


# ---------------------------------------------------------------------------
# CoreSettings default
# ---------------------------------------------------------------------------


class TestLangchainWorkspaceIdDefault:
    """Default value of the new config field."""

    def test_default_is_empty_string(self) -> None:
        """langchain_workspace_id defaults to ''."""
        s = CoreSettings(_env_file=None)
        assert s.langchain_workspace_id == ""

    def test_type_is_str(self) -> None:
        """langchain_workspace_id is of type str."""
        s = CoreSettings()
        assert isinstance(s.langchain_workspace_id, str)


# ---------------------------------------------------------------------------
# No-op paths
# ---------------------------------------------------------------------------


class TestNoOp:
    """core_tracing_configure is a no-op when the gate conditions are not met."""

    def test_noop_when_tracing_disabled(self) -> None:
        """No patch applied when langsmith_enabled is False (flag off)."""
        settings = _make_settings(tracing=False, api_key="key", workspace="ws-id")
        # Inject a fake langsmith so we can detect any accidental patching.
        orig_cls = _FakeClient
        fake_mod = _make_fake_langsmith(orig_cls)
        sys.modules["langsmith"] = fake_mod

        core_tracing_configure(settings)

        assert not core_tracing_mod._PATCHED
        assert fake_mod.Client is orig_cls

    def test_noop_when_api_key_missing(self) -> None:
        """No patch applied when langsmith_enabled is False (key absent)."""
        settings = _make_settings(tracing=True, api_key="", workspace="ws-id")
        orig_cls = _FakeClient
        fake_mod = _make_fake_langsmith(orig_cls)
        sys.modules["langsmith"] = fake_mod

        core_tracing_configure(settings)

        assert not core_tracing_mod._PATCHED
        assert fake_mod.Client is orig_cls

    def test_noop_when_workspace_empty(self) -> None:
        """No patch applied when workspace id is empty string."""
        settings = _make_settings(tracing=True, api_key="key", workspace="")
        orig_cls = _FakeClient
        fake_mod = _make_fake_langsmith(orig_cls)
        sys.modules["langsmith"] = fake_mod

        core_tracing_configure(settings)

        assert not core_tracing_mod._PATCHED
        assert fake_mod.Client is orig_cls

    def test_noop_when_langsmith_not_installed(self, caplog: pytest.LogCaptureFixture) -> None:
        """Warning is logged and no error raised when langsmith is absent."""
        settings = _make_settings(tracing=True, api_key="key", workspace="ws-id")
        # Ensure langsmith is absent.
        sys.modules.pop("langsmith", None)

        # Temporarily block langsmith from being found.
        import builtins

        _real_import = builtins.__import__

        def _blocking_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "langsmith":
                raise ImportError("langsmith not available")
            return _real_import(name, *args, **kwargs)

        builtins.__import__ = _blocking_import
        try:
            with caplog.at_level("WARNING", logger="core.core_tracing"):
                core_tracing_configure(settings)
        finally:
            builtins.__import__ = _real_import

        assert not core_tracing_mod._PATCHED
        assert CORE_TRACING_LOG_UNAVAILABLE in caplog.text


# ---------------------------------------------------------------------------
# Patch applied correctly
# ---------------------------------------------------------------------------


class TestPatchApplied:
    """core_tracing_configure injects X-Tenant-Id when both gate conditions are met."""

    def test_header_injected_on_new_client(self) -> None:
        """A newly constructed Client carries X-Tenant-Id equal to the workspace id."""
        workspace = "3bdafc5c-ws-test"
        settings = _make_settings(tracing=True, api_key="lsv2_sk_test", workspace=workspace)

        fake_mod = _make_fake_langsmith(_FakeClient)
        sys.modules["langsmith"] = fake_mod

        core_tracing_configure(settings)

        assert core_tracing_mod._PATCHED
        client = fake_mod.Client()
        assert client.session.headers.get(CORE_TRACING_HEADER) == workspace

    def test_original_headers_preserved(self) -> None:
        """Pre-existing session headers are not cleared by the patch."""
        workspace = "ws-preserve"
        settings = _make_settings(tracing=True, api_key="lsv2_sk_test", workspace=workspace)

        class _ClientWithExtraHeader:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                self.session = _FakeSession()
                self.session.headers["Authorization"] = "Bearer existing"

        fake_mod = _make_fake_langsmith(_ClientWithExtraHeader)
        sys.modules["langsmith"] = fake_mod

        core_tracing_configure(settings)

        client = fake_mod.Client()
        assert client.session.headers.get("Authorization") == "Bearer existing"
        assert client.session.headers.get(CORE_TRACING_HEADER) == workspace

    def test_patch_is_idempotent(self) -> None:
        """Calling core_tracing_configure twice applies the patch exactly once."""
        workspace = "ws-idempotent"
        settings = _make_settings(tracing=True, api_key="lsv2_sk_test", workspace=workspace)

        call_count = 0
        orig_init = _FakeClient.__init__

        class _CountingClient(_FakeClient):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                nonlocal call_count
                call_count += 1
                orig_init(self, *args, **kwargs)

        fake_mod = _make_fake_langsmith(_CountingClient)
        sys.modules["langsmith"] = fake_mod

        core_tracing_configure(settings)
        first_init = fake_mod.Client.__init__
        core_tracing_configure(settings)  # second call — must be no-op
        second_init = fake_mod.Client.__init__

        # The __init__ should not have been wrapped again.
        assert first_init is second_init

    def test_info_logged_when_patched(self, caplog: pytest.LogCaptureFixture) -> None:
        """INFO log is emitted once when the patch is applied."""
        workspace = "ws-log"
        settings = _make_settings(tracing=True, api_key="lsv2_sk_test", workspace=workspace)

        fake_mod = _make_fake_langsmith(_FakeClient)
        sys.modules["langsmith"] = fake_mod

        with caplog.at_level("INFO", logger="core.core_tracing"):
            core_tracing_configure(settings)

        assert CORE_TRACING_LOG_ENABLED in caplog.text

    def test_workspace_id_not_in_log(self, caplog: pytest.LogCaptureFixture) -> None:
        """Raw workspace id value is never emitted to the log."""
        workspace = "super-secret-ws-id-12345"
        settings = _make_settings(tracing=True, api_key="lsv2_sk_test", workspace=workspace)

        fake_mod = _make_fake_langsmith(_FakeClient)
        sys.modules["langsmith"] = fake_mod

        with caplog.at_level("DEBUG", logger="core.core_tracing"):
            core_tracing_configure(settings)

        assert workspace not in caplog.text
