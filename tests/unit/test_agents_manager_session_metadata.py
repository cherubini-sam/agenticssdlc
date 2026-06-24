"""Hermetic unit tests for session_id -> LangSmith metadata injection in AgentsManager.

Verifies that:
- when session_id is provided, config["metadata"]["session_id"] is set
- configurable["thread_id"] always equals request.task_id (never changed)
- when session_id is None/omitted, no "metadata" key is added to config
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.agents_manager import AgentsManager
from api.schemas.api_schemas_task import ApiSchemasTaskRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    task_id: str = "task-abc-123", content: str = "test task"
) -> ApiSchemasTaskRequest:
    return ApiSchemasTaskRequest(task_id=task_id, content=content)


async def _drain(gen) -> None:
    """Exhaust an async generator."""
    try:
        async for _ in gen:
            pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def manager() -> AgentsManager:
    """AgentsManager with a fully mocked internal graph."""
    mock_graph = MagicMock()

    # astream_events must be an async generator that yields nothing
    async def _empty_astream(*args: Any, **kwargs: Any):
        return
        yield  # make it an async generator

    mock_graph.astream_events = _empty_astream
    # ainvoke never called in stream tests, but set it up for run tests
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "task_id": "task-abc-123",
            "result": "ok",
            "confidence": 1.0,
            "approved": True,
            "error": None,
            "messages": [],
            "artifact_uri": None,
        }
    )
    return AgentsManager(mock_graph)


# ---------------------------------------------------------------------------
# agents_manager_stream_events — config capture tests
# ---------------------------------------------------------------------------


class TestStreamEventsMetadata:
    """Config dict passed to astream_events carries correct metadata."""

    def test_session_id_present_sets_metadata(self, manager: AgentsManager) -> None:
        """When session_id is provided, metadata["session_id"] equals it."""
        captured: list[dict] = []

        async def _capture_astream(input_, *, config, **kwargs):
            captured.append(config)
            return
            yield

        manager._graph.astream_events = _capture_astream

        request = _make_request(task_id="t-001")
        asyncio.get_event_loop().run_until_complete(
            _drain(manager.agents_manager_stream_events(request, session_id="session-XYZ"))
        )

        assert len(captured) == 1
        cfg = captured[0]
        assert cfg["metadata"]["session_id"] == "session-XYZ"
        assert cfg["configurable"]["thread_id"] == "t-001"

    def test_session_id_none_omits_metadata(self, manager: AgentsManager) -> None:
        """When session_id is None, no metadata key is added to config."""
        captured: list[dict] = []

        async def _capture_astream(input_, *, config, **kwargs):
            captured.append(config)
            return
            yield

        manager._graph.astream_events = _capture_astream

        request = _make_request(task_id="t-002")
        asyncio.get_event_loop().run_until_complete(
            _drain(manager.agents_manager_stream_events(request, session_id=None))
        )

        assert len(captured) == 1
        cfg = captured[0]
        assert "metadata" not in cfg
        assert cfg["configurable"]["thread_id"] == "t-002"

    def test_session_id_omitted_omits_metadata(self, manager: AgentsManager) -> None:
        """When session_id is not passed at all, no metadata key is added (backward compat)."""
        captured: list[dict] = []

        async def _capture_astream(input_, *, config, **kwargs):
            captured.append(config)
            return
            yield

        manager._graph.astream_events = _capture_astream

        request = _make_request(task_id="t-003")
        asyncio.get_event_loop().run_until_complete(
            _drain(manager.agents_manager_stream_events(request))
        )

        assert len(captured) == 1
        cfg = captured[0]
        assert "metadata" not in cfg
        assert cfg["configurable"]["thread_id"] == "t-003"

    def test_thread_id_unchanged_when_session_id_set(self, manager: AgentsManager) -> None:
        """Providing session_id must never alter configurable.thread_id."""
        captured: list[dict] = []

        async def _capture_astream(input_, *, config, **kwargs):
            captured.append(config)
            return
            yield

        manager._graph.astream_events = _capture_astream

        task_id = "immutable-task-id"
        request = _make_request(task_id=task_id)
        asyncio.get_event_loop().run_until_complete(
            _drain(manager.agents_manager_stream_events(request, session_id="some-session"))
        )

        cfg = captured[0]
        assert cfg["configurable"]["thread_id"] == task_id
        assert cfg["metadata"]["session_id"] == "some-session"

    def test_empty_string_session_id_omits_metadata(self, manager: AgentsManager) -> None:
        """An empty string is falsy; metadata must not be set."""
        captured: list[dict] = []

        async def _capture_astream(input_, *, config, **kwargs):
            captured.append(config)
            return
            yield

        manager._graph.astream_events = _capture_astream

        request = _make_request(task_id="t-004")
        asyncio.get_event_loop().run_until_complete(
            _drain(manager.agents_manager_stream_events(request, session_id=""))
        )

        cfg = captured[0]
        assert "metadata" not in cfg


# ---------------------------------------------------------------------------
# agents_manager_run — config capture tests (parity)
# ---------------------------------------------------------------------------


class TestRunMetadata:
    """Config dict passed to ainvoke carries correct metadata (parity with stream path)."""

    def test_run_session_id_present_sets_metadata(self, manager: AgentsManager) -> None:
        captured: list[dict] = []

        async def _capture_ainvoke(state, config, **kwargs):
            captured.append(config)
            return {
                "task_id": state["task_id"],
                "result": "ok",
                "confidence": 1.0,
                "approved": True,
                "error": None,
                "messages": [],
                "artifact_uri": None,
            }

        manager._graph.ainvoke = _capture_ainvoke

        request = _make_request(task_id="t-run-001")
        asyncio.get_event_loop().run_until_complete(
            manager.agents_manager_run(request, session_id="run-session-ABC")
        )

        assert len(captured) == 1
        cfg = captured[0]
        assert cfg["metadata"]["session_id"] == "run-session-ABC"
        assert cfg["configurable"]["thread_id"] == "t-run-001"

    def test_run_session_id_none_omits_metadata(self, manager: AgentsManager) -> None:
        captured: list[dict] = []

        async def _capture_ainvoke(state, config, **kwargs):
            captured.append(config)
            return {
                "task_id": state["task_id"],
                "result": "ok",
                "confidence": 1.0,
                "approved": True,
                "error": None,
                "messages": [],
                "artifact_uri": None,
            }

        manager._graph.ainvoke = _capture_ainvoke

        request = _make_request(task_id="t-run-002")
        asyncio.get_event_loop().run_until_complete(manager.agents_manager_run(request))

        assert len(captured) == 1
        cfg = captured[0]
        assert "metadata" not in cfg
        assert cfg["configurable"]["thread_id"] == "t-run-002"
