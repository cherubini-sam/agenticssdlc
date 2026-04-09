"""AgentsArchitect plan drafting via LLM."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.agents_architect import AgentsArchitect as ArchitectAgent


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
