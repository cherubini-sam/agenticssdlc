"""AgentsBase exponential-backoff retry on ResourceExhausted."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.api_core.exceptions import ResourceExhausted

from agents.agents_base import AgentsBase as BaseAgent


class TestBaseAgent:
    """Tests for AgentsBase retry logic on quota errors."""

    @pytest.mark.asyncio
    async def test_call_llm_retries_on_resource_exhausted(self) -> None:
        """Retries once after ResourceExhausted and returns the successful response."""

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = [
            ResourceExhausted("quota exceeded"),
            MagicMock(content="success"),
        ]

        agent = BaseAgent.__new__(BaseAgent)
        agent.llm = mock_llm
        agent.agent_name = "TEST"
        agent.logger = MagicMock()
        agent._role_doc = ""

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await agent._agents_base_call_llm(["test prompt"])

        assert result == "success"
        assert mock_llm.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_call_llm_raises_after_max_retries(self) -> None:
        """Raises an exception once the maximum retry count is exhausted."""

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = ResourceExhausted("quota exceeded")

        agent = BaseAgent.__new__(BaseAgent)
        agent.llm = mock_llm
        agent.agent_name = "TEST"
        agent.logger = MagicMock()
        agent._role_doc = ""

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises((ResourceExhausted, RuntimeError)):
                await agent._agents_base_call_llm(["test prompt"])


class TestRequireContextSections:
    """Tests for the fail-closed context-availability guard."""

    def test_returns_missing_markers_when_absent(self) -> None:
        missing = BaseAgent._require_context_sections(
            "some context without the marker",
            ["INTEGRATION & BENCHMARK AUTHORITY", "FEEDBACK LOOP"],
        )
        assert missing == ["INTEGRATION & BENCHMARK AUTHORITY", "FEEDBACK LOOP"]

    def test_returns_empty_when_all_present(self) -> None:
        ctx = "prefix INTEGRATION & BENCHMARK AUTHORITY mid FEEDBACK LOOP tail"
        missing = BaseAgent._require_context_sections(
            ctx, ["INTEGRATION & BENCHMARK AUTHORITY", "FEEDBACK LOOP"]
        )
        assert missing == []

    def test_returns_only_the_unmatched_subset(self) -> None:
        ctx = "FEEDBACK LOOP only"
        missing = BaseAgent._require_context_sections(
            ctx, ["INTEGRATION & BENCHMARK AUTHORITY", "FEEDBACK LOOP"]
        )
        assert missing == ["INTEGRATION & BENCHMARK AUTHORITY"]

    def test_none_context_treated_as_empty(self) -> None:
        missing = BaseAgent._require_context_sections(None, ["X"])  # type: ignore[arg-type]
        assert missing == ["X"]


class TestBuildSystemPrompt:
    """Tests for _agents_base_build_system_prompt role-doc injection."""

    def _make_agent(self, role_doc: str) -> "BaseAgent":
        agent = BaseAgent.__new__(BaseAgent)
        agent.llm = MagicMock()
        agent.agent_name = "TEST"
        agent.logger = MagicMock()
        agent._role_doc = role_doc
        return agent

    def test_returns_base_when_no_role_doc(self) -> None:
        agent = self._make_agent("")
        result = agent._agents_base_build_system_prompt("base prompt")
        assert result == "base prompt"

    def test_appends_role_doc_with_separator(self) -> None:
        agent = self._make_agent("## My Role\n\nContent here.")
        result = agent._agents_base_build_system_prompt("base prompt")
        assert result.startswith("base prompt")
        assert "## My Role" in result
        assert "---" in result

    def test_injects_doc_vars_into_role_doc(self) -> None:
        agent = self._make_agent("Threshold is {threshold_value}.")
        result = agent._agents_base_build_system_prompt("base", threshold_value="0.9")
        assert "Threshold is 0.9." in result

    def test_doc_vars_do_not_affect_json_blocks(self) -> None:
        agent = self._make_agent('```json\n{"active_agent": "REFLECTOR"}\n```')
        result = agent._agents_base_build_system_prompt("base", confidence_threshold="0.9")
        assert '{"active_agent": "REFLECTOR"}' in result

    def test_unknown_placeholder_left_intact(self) -> None:
        agent = self._make_agent("Value: {some_key}.")
        result = agent._agents_base_build_system_prompt("base", other_key="x")
        assert "{some_key}" in result


class TestDetectMissingContingentSections:
    """Tests for the plan-vs-context cross-check the ENGINEER uses."""

    def test_flags_marker_in_plan_but_not_context(self) -> None:
        missing = BaseAgent._detect_missing_contingent_sections(
            plan="contingent on INTEGRATION & BENCHMARK AUTHORITY",
            context="empty",
            known_sections=["INTEGRATION & BENCHMARK AUTHORITY", "FEEDBACK LOOP"],
        )
        assert missing == ["INTEGRATION & BENCHMARK AUTHORITY"]

    def test_passes_when_marker_present_in_both(self) -> None:
        missing = BaseAgent._detect_missing_contingent_sections(
            plan="contingent on INTEGRATION & BENCHMARK AUTHORITY",
            context="INTEGRATION & BENCHMARK AUTHORITY is here",
            known_sections=["INTEGRATION & BENCHMARK AUTHORITY"],
        )
        assert missing == []

    def test_ignores_marker_not_in_plan(self) -> None:
        missing = BaseAgent._detect_missing_contingent_sections(
            plan="no protocol references",
            context="no protocol references",
            known_sections=["INTEGRATION & BENCHMARK AUTHORITY"],
        )
        assert missing == []

    def test_handles_empty_inputs(self) -> None:
        missing = BaseAgent._detect_missing_contingent_sections(
            plan=None, context=None, known_sections=["X"]  # type: ignore[arg-type]
        )
        assert missing == []
