"""Pure routing functions in AgentsManager no LLM, no I/O."""

from __future__ import annotations

import pytest

from agents.agents_manager import (
    _agents_manager_increment_retry,
    _agents_manager_route_after_critique,
    _agents_manager_route_after_protocol,
    _agents_manager_route_after_verify,
)


def _make_state(**overrides) -> dict:
    """Minimal AgentsState-shaped dict with sensible defaults."""

    base: dict = {
        "task_id": "t-001",
        "content": "Do something",
        "phase": 0,
        "messages": [],
        "active_agent": "MANAGER",
        "context": None,
        "plan": None,
        "critique": None,
        "result": None,
        "confidence": 0.0,
        "approved": False,
        "retry_count": 0,
        "error": None,
        "protocol_status": None,
        "protocol_violations": None,
        "confidence_threshold": None,
        "validator_confidence_threshold": None,
        "max_retries_override": None,
        "verbosity": None,
    }
    base.update(overrides)
    return base


class TestRouteAfterProtocol:
    """Routing decisions after the protocol validation phase."""

    def test_green_routes_to_task(self) -> None:
        """system_green status routes to the 'task' node."""

        state = _make_state(protocol_status="system_green")
        assert _agents_manager_route_after_protocol(state) == "task"

    def test_error_routes_to_end_failed(self) -> None:
        """system_error status routes to 'end_failed'."""

        state = _make_state(protocol_status="system_error")
        assert _agents_manager_route_after_protocol(state) == "end_failed"

    def test_none_status_routes_to_end_failed(self) -> None:
        """None protocol_status routes to 'end_failed'."""

        state = _make_state(protocol_status=None)
        assert _agents_manager_route_after_protocol(state) == "end_failed"


class TestRouteAfterCritique:
    """Routing decisions after the reflector critique phase."""

    def test_no_critique_routes_to_execute(self) -> None:
        """Missing critique dict routes directly to 'execute'."""

        state = _make_state(critique=None)
        assert _agents_manager_route_after_critique(state) == "execute"

    def test_approved_true_routes_to_execute(self) -> None:
        """Critique with approved=True routes to 'execute' regardless of confidence."""

        state = _make_state(
            critique={"approved": True, "confidence": 0.5, "errors": []},
            retry_count=0,
        )
        assert _agents_manager_route_after_critique(state) == "execute"

    def test_high_confidence_routes_to_execute(self) -> None:
        """Confidence above threshold routes to 'execute'."""

        state = _make_state(
            critique={"confidence": 0.95, "errors": []},
            retry_count=0,
        )
        assert _agents_manager_route_after_critique(state) == "execute"

    def test_low_confidence_with_retries_routes_to_retry(self) -> None:
        """Low confidence with retries remaining routes to 'retry_increment'."""

        state = _make_state(
            critique={"confidence": 0.3, "errors": ["bad plan"], "approved": False},
            retry_count=0,
        )
        assert _agents_manager_route_after_critique(state) == "retry_increment"

    def test_retries_exhausted_forces_execute(self) -> None:
        """Exhausted retries force 'execute' even when confidence is low."""

        # MAX_RETRIES defaults to 3; at retry_count=3 we give up and proceed
        state = _make_state(
            critique={"confidence": 0.2, "errors": ["really bad"], "approved": False},
            retry_count=3,
        )
        assert _agents_manager_route_after_critique(state) == "execute"

    def test_custom_confidence_threshold_respected(self) -> None:
        """Confidence above a custom threshold routes to 'execute'."""

        # 0.7 beats custom threshold 0.65
        state = _make_state(
            critique={"confidence": 0.7, "errors": []},
            confidence_threshold=0.65,
            retry_count=0,
        )
        assert _agents_manager_route_after_critique(state) == "execute"

    def test_custom_max_retries_override(self) -> None:
        """max_retries_override=1 forces 'execute' when retry_count reaches it."""

        # max_retries_override=1, retry_count=1 -> forced execute
        state = _make_state(
            critique={"confidence": 0.1, "errors": ["bad"], "approved": False},
            retry_count=1,
            max_retries_override=1,
        )
        assert _agents_manager_route_after_critique(state) == "execute"


class TestRouteAfterVerify:
    """Routing decisions after the validator verification phase."""

    def test_no_error_routes_to_end_success(self) -> None:
        """No error routes to 'end_success'."""

        state = _make_state(error=None, retry_count=0)
        assert _agents_manager_route_after_verify(state) == "end_success"

    def test_error_with_retries_available_routes_to_retry(self) -> None:
        """Validation error with retries remaining routes to 'retry_increment'."""

        state = _make_state(error="Validation failed", retry_count=0)
        assert _agents_manager_route_after_verify(state) == "retry_increment"

    def test_error_retries_exhausted_force_accept(self) -> None:
        """Validation error after exhausting default retries forces 'end_success'."""

        state = _make_state(error="Validation failed", retry_count=3)
        assert _agents_manager_route_after_verify(state) == "end_success"

    def test_error_custom_max_retries_exhausted(self) -> None:
        """Validation error after exhausting custom max_retries forces 'end_success'."""

        state = _make_state(
            error="Validation failed",
            retry_count=2,
            max_retries_override=2,
        )
        assert _agents_manager_route_after_verify(state) == "end_success"


class TestIncrementRetry:
    """Tests for the retry counter increment helper."""

    @pytest.mark.asyncio
    async def test_increments_counter(self) -> None:
        """retry_count is incremented by 1 from a non-zero value."""

        state = _make_state(retry_count=1)
        result = await _agents_manager_increment_retry(state)

        assert result["retry_count"] == 2

    @pytest.mark.asyncio
    async def test_increments_from_zero(self) -> None:
        """retry_count advances from 0 to 1 on first retry."""

        state = _make_state(retry_count=0)
        result = await _agents_manager_increment_retry(state)

        assert result["retry_count"] == 1
