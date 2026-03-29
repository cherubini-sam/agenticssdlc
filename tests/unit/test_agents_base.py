"""AgentsBase exponential-backoff retry on ResourceExhausted."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_call_llm_retries_on_resource_exhausted(self) -> None:
        from google.api_core.exceptions import ResourceExhausted

        from agents.agents_base import AgentsBase as BaseAgent

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = [
            ResourceExhausted("quota exceeded"),
            MagicMock(content="success"),
        ]

        agent = BaseAgent.__new__(BaseAgent)
        agent.llm = mock_llm
        agent.agent_name = "TEST"
        agent.logger = MagicMock()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await agent._agents_base_call_llm(["test prompt"])

        assert result == "success"
        assert mock_llm.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_call_llm_raises_after_max_retries(self) -> None:
        from google.api_core.exceptions import ResourceExhausted

        from agents.agents_base import AgentsBase as BaseAgent

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = ResourceExhausted("quota exceeded")

        agent = BaseAgent.__new__(BaseAgent)
        agent.llm = mock_llm
        agent.agent_name = "TEST"
        agent.logger = MagicMock()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises((ResourceExhausted, RuntimeError)):
                await agent._agents_base_call_llm(["test prompt"])
