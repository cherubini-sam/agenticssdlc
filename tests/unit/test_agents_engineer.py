"""AgentsEngineer plan execution via LLM."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestEngineerAgent:
    @pytest.mark.asyncio
    async def test_execute_returns_string(self) -> None:
        from agents.agents_engineer import AgentsEngineer as EngineerAgent

        agent = EngineerAgent.__new__(EngineerAgent)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="Implementation complete."))
        agent.agent_name = "ENGINEER"
        agent.logger = MagicMock()

        result = await agent.agents_engineer_execute("## Plan", [], "Build a REST API")
        assert isinstance(result, str)
