"""AgentsReflector 4-persona critique pipeline (judge/critic/refiner/curator)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestReflectorAgent:
    @pytest.mark.asyncio
    async def test_audit_returns_confidence(self) -> None:
        from agents.agents_reflector import AgentsReflector

        agent = AgentsReflector.__new__(AgentsReflector)
        agent.llm = AsyncMock()
        # Each persona responds in sequence: judge -> critic -> refiner -> curator
        agent.llm.ainvoke = AsyncMock(
            side_effect=[
                MagicMock(content='{"errors": [], "severity": "NONE"}'),
                MagicMock(content='{"fixes": [], "suggestions": []}'),
                MagicMock(content='{"refined_plan": "## Refined Plan", "improvements": []}'),
                MagicMock(
                    content=(
                        '{"approved": true, "confidence": 0.90, "critique": "Solid work",'
                        ' "refined_output": "Refined result", "metadata": {}}'
                    )
                ),
            ]
        )
        agent.agent_name = "REFLECTOR"
        agent.logger = MagicMock()

        result = await agent.agents_reflector_critique("## Plan", "context", "task")
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
