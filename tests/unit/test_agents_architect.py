"""AgentsArchitect plan drafting via LLM."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.agents_architect import AgentsArchitect as ArchitectAgent
from agents.agents_utils import (
    AGENTS_ARCHITECT_CONTEXT_MISSING_STATUS,
    AGENTS_ARCHITECT_REQUIRED_SECTIONS,
)


class TestArchitectAgent:
    """Tests for AgentsArchitect plan-drafting behaviour."""

    @pytest.mark.asyncio
    async def test_draft_plan_returns_string(self) -> None:
        """LLM response is returned as a non-empty string."""

        agent = ArchitectAgent.__new__(ArchitectAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="## Plan\n1. Step one\n2. Step two")
        )
        agent.agent_name = "ARCHITECT"
        agent.logger = MagicMock()

        result = await agent.agents_architect_draft_plan("Build a REST API", [])
        assert isinstance(result, str)
        assert len(result) > 0


class TestArchitectContextGuard:
    """Tests for the fail-closed required-sections guard."""

    @pytest.mark.asyncio
    async def test_refuses_when_required_section_absent(self) -> None:
        """When callers opt in to the guard, a missing marker short-circuits the LLM call."""

        agent = ArchitectAgent.__new__(ArchitectAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="should not run"))
        agent.agent_name = "ARCHITECT"
        agent.logger = MagicMock()

        result = await agent.agents_architect_draft_plan(
            task="Audit REFLECTOR",
            context="only partial context, no protocol sections here",
            required_sections=AGENTS_ARCHITECT_REQUIRED_SECTIONS,
        )

        assert AGENTS_ARCHITECT_CONTEXT_MISSING_STATUS in result
        assert "INTEGRATION & BENCHMARK AUTHORITY" in result
        assert "FEEDBACK LOOP" in result
        agent.llm.ainvoke.assert_not_called()
        agent.logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_proceeds_when_all_sections_present(self) -> None:
        """Guard is transparent once the context contains every required marker."""

        agent = ArchitectAgent.__new__(ArchitectAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="## Plan\n1. ok"))
        agent.agent_name = "ARCHITECT"
        agent.logger = MagicMock()

        context = "INTEGRATION & BENCHMARK AUTHORITY ... FEEDBACK LOOP ... details"
        result = await agent.agents_architect_draft_plan(
            task="Audit REFLECTOR",
            context=context,
            required_sections=AGENTS_ARCHITECT_REQUIRED_SECTIONS,
        )

        assert "## Plan" in result
        agent.llm.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_guard_disabled_by_default(self) -> None:
        """Existing callers (no required_sections kwarg) keep the pre-fix behaviour."""

        agent = ArchitectAgent.__new__(ArchitectAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="## Plan\n1. ok"))
        agent.agent_name = "ARCHITECT"
        agent.logger = MagicMock()

        result = await agent.agents_architect_draft_plan("task", "empty context")

        assert "## Plan" in result
        agent.llm.ainvoke.assert_awaited_once()
