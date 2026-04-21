"""Fail-closed refusal detection and routing in AgentsManager — no LLM, no I/O."""

from __future__ import annotations

import pytest

from agents.agents_manager import (
    _agents_manager_extract_missing_sections,
    _agents_manager_is_refusal,
    _agents_manager_route_after_architect,
    _agents_manager_route_after_execute,
)
from agents.agents_utils import AGENTS_REFUSAL_STATUS_PREFIX

REFUSAL_SAMPLE: str = (
    f"{AGENTS_REFUSAL_STATUS_PREFIX}\n"
    "missing_sections: INTEGRATION & BENCHMARK AUTHORITY, FEEDBACK LOOP\n"
    "The ENGINEER refused to execute because the plan depends on the sections above."
)


def _make_state(**overrides) -> dict:
    """Minimal AgentsState-shaped dict with sensible defaults."""

    base: dict = {
        "task_id": "t-refusal",
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


class TestIsRefusal:
    """Refusal classifier used by post-ARCHITECT and post-EXECUTE routers."""

    def test_canonical_refusal_prefix_detected(self) -> None:
        """Output beginning with the canonical prefix is classified as a refusal."""

        assert _agents_manager_is_refusal(REFUSAL_SAMPLE) is True

    def test_leading_whitespace_tolerated(self) -> None:
        """Leading whitespace does not break the classifier."""

        assert _agents_manager_is_refusal("   \n" + REFUSAL_SAMPLE) is True

    def test_normal_plan_text_not_refusal(self) -> None:
        """A real plan that happens to mention 'status' is not misclassified."""

        plan = "## Plan\n1. Step one.\n2. Step two — status checks included."
        assert _agents_manager_is_refusal(plan) is False

    def test_empty_and_none_are_not_refusal(self) -> None:
        """Empty string and None are safe defaults."""

        assert _agents_manager_is_refusal(None) is False
        assert _agents_manager_is_refusal("") is False


class TestExtractMissingSections:
    """Parser for the missing_sections line in refusal preambles."""

    def test_extracts_comma_separated_list(self) -> None:
        """Comma-separated section markers are returned verbatim."""

        extracted = _agents_manager_extract_missing_sections(REFUSAL_SAMPLE)
        assert extracted == "INTEGRATION & BENCHMARK AUTHORITY, FEEDBACK LOOP"

    def test_missing_line_returns_unknown_sentinel(self) -> None:
        """A refusal that omits the missing_sections line returns '<unknown>'."""

        refusal = f"{AGENTS_REFUSAL_STATUS_PREFIX}\nno details provided."
        assert _agents_manager_extract_missing_sections(refusal) == "<unknown>"


class TestRouteAfterArchitect:
    """ARCHITECT refusal short-circuits to END_FAILED, otherwise proceeds to REVIEW."""

    def test_refusal_plan_routes_to_end_failed(self) -> None:
        """A plan carrying the refusal preamble bypasses REFLECTOR entirely."""

        state = _make_state(plan=REFUSAL_SAMPLE)
        assert _agents_manager_route_after_architect(state) == "end_failed"

    def test_real_plan_routes_to_review(self) -> None:
        """A legitimate plan flows into the REFLECTOR critique phase."""

        state = _make_state(plan="## Plan\n1. Real step.")
        assert _agents_manager_route_after_architect(state) == "review"


class TestRouteAfterExecute:
    """ENGINEER refusal short-circuits to END_FAILED, otherwise proceeds to VERIFY."""

    def test_refusal_result_routes_to_end_failed(self) -> None:
        """A refusal result bypasses VALIDATOR to avoid the passed-on-refusal bug."""

        state = _make_state(result=REFUSAL_SAMPLE)
        assert _agents_manager_route_after_execute(state) == "end_failed"

    def test_real_result_routes_to_verify(self) -> None:
        """A legitimate result flows into the VALIDATOR QA phase."""

        state = _make_state(result="def run():\n    return 42")
        assert _agents_manager_route_after_execute(state) == "verify"


class TestValidatorRefusalShortCircuit:
    """VALIDATOR returns failed/0.0 deterministically on a refusal preamble."""

    @pytest.mark.asyncio
    async def test_refusal_skips_llm_and_fails(self) -> None:
        """Refusal input returns failed verdict with zero score, no LLM call."""

        from unittest.mock import AsyncMock, MagicMock

        from agents.agents_validator import (
            AGENTS_VALIDATOR_ISSUE_EXECUTION_REFUSED,
            AGENTS_VALIDATOR_VERDICT_FAILED,
            AgentsValidator,
        )

        agent = AgentsValidator.__new__(AgentsValidator)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock()
        agent.agent_name = "VALIDATOR"
        agent.logger = MagicMock()

        verdict = await agent.agents_validator_verify(result=REFUSAL_SAMPLE, plan="any", task="any")

        assert verdict["verdict"] == AGENTS_VALIDATOR_VERDICT_FAILED
        assert verdict["score"] == 0.0
        assert AGENTS_VALIDATOR_ISSUE_EXECUTION_REFUSED in verdict["issues"]
        agent.llm.ainvoke.assert_not_called()


class TestProtocolSectionPreambleInvariant:
    """The injected preamble must literally contain every guarded section marker."""

    def test_all_required_markers_present(self) -> None:
        """Empty result from the validator means the preamble satisfies both guards."""

        from agents.agents_protocol_sections import agents_protocol_sections_validate_preamble

        assert agents_protocol_sections_validate_preamble() == []
