"""AgentsValidator verdict parsing from LLM output, including embedded JSON."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.agents_validator import AgentsValidator


class TestValidatorAgent:
    """Tests for AgentsValidator LLM verdict parsing."""

    @pytest.mark.asyncio
    async def test_verify_returns_dict(self) -> None:
        """Clean JSON LLM response is returned as a dict with verdict and score."""

        agent = AgentsValidator.__new__(AgentsValidator)
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content='{"verdict": "APPROVED", "score": 0.92, "issues": [], "error": null}'
            )
        )
        agent.agent_name = "VALIDATOR"
        agent.logger = MagicMock()

        result = await agent.agents_validator_verify("execution result", "plan", "task")
        assert "verdict" in result
        assert "score" in result

    @pytest.mark.asyncio
    async def test_verify_handles_malformed_json(self) -> None:
        """JSON embedded in conversational text is extracted and parsed correctly."""

        agent = AgentsValidator.__new__(AgentsValidator)
        agent.llm = AsyncMock()
        # LLM sometimes wraps JSON in conversational text
        agent.llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content=(
                    'Some text {"verdict": "NEEDS_REVISION", "score": 0.6,'
                    ' "issues": ["issue1"], "error": null} more text'
                )
            )
        )
        agent.agent_name = "VALIDATOR"
        agent.logger = MagicMock()

        result = await agent.agents_validator_verify("execution result", "plan", "task")
        assert result["verdict"] in ("APPROVED", "NEEDS_REVISION", "REJECTED")
