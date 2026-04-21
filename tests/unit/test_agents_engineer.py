"""AgentsEngineer plan execution via LLM."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.agents_engineer import AgentsEngineer as EngineerAgent
from agents.agents_utils import AGENTS_ENGINEER_CONTEXT_MISSING_STATUS


class TestEngineerAgent:
    """Tests for AgentsEngineer plan execution behaviour."""

    @pytest.mark.asyncio
    async def test_execute_returns_string(self) -> None:
        """LLM execution result is returned as a string."""

        agent = EngineerAgent.__new__(EngineerAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="Implementation complete."))
        agent.agent_name = "ENGINEER"
        agent.logger = MagicMock()

        result = await agent.agents_engineer_execute("## Plan", [], "Build a REST API")
        assert isinstance(result, str)


class TestEngineerContingencyGuard:
    """Tests for the fail-closed plan-vs-context contingency check."""

    @pytest.mark.asyncio
    async def test_refuses_when_plan_depends_on_missing_section(self) -> None:
        """Plan mentions a known protocol section; context does not → refuse before the LLM."""

        agent = EngineerAgent.__new__(EngineerAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="should not run"))
        agent.agent_name = "ENGINEER"
        agent.logger = MagicMock()

        plan = (
            "## 0. Pre-computation & Context Gathering\n"
            "This step is contingent on the availability of "
            "INTEGRATION & BENCHMARK AUTHORITY and FEEDBACK LOOP."
        )
        context = "irrelevant context without the protocol sections"

        result = await agent.agents_engineer_execute(plan, context)

        assert AGENTS_ENGINEER_CONTEXT_MISSING_STATUS in result
        assert "INTEGRATION & BENCHMARK AUTHORITY" in result
        assert "FEEDBACK LOOP" in result
        agent.llm.ainvoke.assert_not_called()
        agent.logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_proceeds_when_plan_referenced_sections_are_present(self) -> None:
        """If the context literally contains every referenced section, the LLM is invoked."""

        agent = EngineerAgent.__new__(EngineerAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="done"))
        agent.agent_name = "ENGINEER"
        agent.logger = MagicMock()

        plan = "Contingent on INTEGRATION & BENCHMARK AUTHORITY and FEEDBACK LOOP."
        context = "INTEGRATION & BENCHMARK AUTHORITY ... FEEDBACK LOOP ... full text"

        result = await agent.agents_engineer_execute(plan, context)

        assert result == "done"
        agent.llm.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ignores_sections_not_referenced_by_plan(self) -> None:
        """A plan that never mentions the markers must NOT be blocked by their absence."""

        agent = EngineerAgent.__new__(EngineerAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="done"))
        agent.agent_name = "ENGINEER"
        agent.logger = MagicMock()

        plan = "Implement a Pandas function to ingest JSON and export to Parquet."
        context = "pandas DataFrame examples, no protocol sections at all"

        result = await agent.agents_engineer_execute(plan, context)

        assert result == "done"
        agent.llm.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_guard_can_be_disabled(self) -> None:
        """Passing ``known_sections=[]`` restores the pre-guard behaviour."""

        agent = EngineerAgent.__new__(EngineerAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="done"))
        agent.agent_name = "ENGINEER"
        agent.logger = MagicMock()

        plan = "Plan references INTEGRATION & BENCHMARK AUTHORITY."
        context = "no protocol sections"

        result = await agent.agents_engineer_execute(plan, context, known_sections=[])

        assert result == "done"
        agent.llm.ainvoke.assert_awaited_once()
