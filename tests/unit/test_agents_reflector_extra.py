"""Parse logic and fast/slow path branching in AgentsReflector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.agents_reflector import AgentsReflector


class TestAgentsReflectorParse:
    """Tests for the static _agents_reflector_parse JSON extraction helper."""

    def test_valid_json_returns_parsed(self) -> None:
        """Clean JSON string is parsed into the expected dict."""

        raw = '{"confidence": 0.9, "errors": [], "severity": "NONE"}'
        result = AgentsReflector._agents_reflector_parse(raw, {})

        assert result["confidence"] == 0.9
        assert result["errors"] == []

    def test_json_embedded_in_text_returns_parsed(self) -> None:
        """JSON embedded in surrounding text is extracted and parsed."""

        raw = 'Some preamble {"confidence": 0.7, "errors": ["missing step"]} trailing text'
        result = AgentsReflector._agents_reflector_parse(raw, {})

        assert result["confidence"] == 0.7
        assert "missing step" in result["errors"]

    def test_malformed_json_returns_default(self) -> None:
        """Malformed JSON falls back to the supplied default dict."""

        raw = "{this is not valid json}"
        default = {"confidence": 0.5}
        result = AgentsReflector._agents_reflector_parse(raw, default)

        assert result == default

    def test_no_json_in_string_returns_default(self) -> None:
        """Plain text with no JSON object falls back to the default dict."""

        raw = "No JSON here at all"
        default = {"confidence": 0.0}
        result = AgentsReflector._agents_reflector_parse(raw, default)

        assert result == default

    def test_empty_string_returns_default(self) -> None:
        """Empty string falls back to the default dict."""

        default = {"fallback": True}
        result = AgentsReflector._agents_reflector_parse("", default)

        assert result == default

    def test_multiline_json_parsed(self) -> None:
        """Multi-line JSON string is parsed correctly."""

        raw = '{\n  "confidence": 0.85,\n  "errors": []\n}'
        result = AgentsReflector._agents_reflector_parse(raw, {})

        assert result["confidence"] == 0.85


class TestAgentsReflectorFastPath:
    """High confidence or SKIP label -> fast path (keep original plan).
    Low confidence -> slow path (use the LLM's refined plan)."""

    @pytest.mark.asyncio
    async def test_fast_path_high_confidence_uses_original_plan(self) -> None:
        """High-confidence LLM response keeps the original plan unchanged."""

        agent = AgentsReflector.__new__(AgentsReflector)
        agent.agent_name = "REFLECTOR"
        agent.logger = MagicMock()

        llm_response = MagicMock(
            content='{"confidence": 0.95, "errors": [], "severity": "NONE", '
            '"suggestions": [], "refined_plan": "SKIP", '
            '"improvements": [], "reuse_pattern": "", "knowledge_atom": ""}'
        )
        agent.llm = MagicMock()
        agent.llm.ainvoke = AsyncMock(return_value=llm_response)

        original_plan = "## Original Plan\n1. Do X\n2. Do Y"
        result = await agent.agents_reflector_critique(original_plan, "context", "task")

        assert result["confidence"] >= 0.9
        assert result["refined_plan"] == original_plan

    @pytest.mark.asyncio
    async def test_fast_path_skip_label_uses_original_plan(self) -> None:
        """SKIP label in refined_plan triggers fast path even at moderate confidence."""

        agent = AgentsReflector.__new__(AgentsReflector)
        agent.agent_name = "REFLECTOR"
        agent.logger = MagicMock()

        # SKIP label triggers fast path even at moderate confidence
        llm_response = MagicMock(
            content='{"confidence": 0.85, "errors": [], "severity": "LOW", '
            '"suggestions": [], "refined_plan": "SKIP", '
            '"improvements": [], "reuse_pattern": "", "knowledge_atom": "lesson"}'
        )
        agent.llm = MagicMock()
        agent.llm.ainvoke = AsyncMock(return_value=llm_response)

        original_plan = "## Plan"
        result = await agent.agents_reflector_critique(original_plan, "", "task")

        assert result["refined_plan"] == original_plan

    @pytest.mark.asyncio
    async def test_slow_path_low_confidence_uses_refined_plan(self) -> None:
        """Low-confidence response triggers slow path and returns the refined plan."""

        agent = AgentsReflector.__new__(AgentsReflector)
        agent.agent_name = "REFLECTOR"
        agent.logger = MagicMock()

        llm_response = MagicMock(
            content='{"confidence": 0.6, "errors": ["missing error handling"], '
            '"severity": "MEDIUM", "suggestions": ["add try/except"], '
            '"refined_plan": "## Improved Plan\\n1. Do X better", '
            '"improvements": ["added error handling"], '
            '"reuse_pattern": "template", "knowledge_atom": "lesson"}'
        )
        agent.llm = MagicMock()
        agent.llm.ainvoke = AsyncMock(return_value=llm_response)

        result = await agent.agents_reflector_critique("## Plan", "ctx", "task")

        assert result["confidence"] == 0.6
        assert "Improved" in result["refined_plan"]
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_critique_returns_required_keys(self) -> None:
        """Critique result contains all required output keys."""

        agent = AgentsReflector.__new__(AgentsReflector)
        agent.agent_name = "REFLECTOR"
        agent.logger = MagicMock()

        llm_response = MagicMock(
            content='{"confidence": 0.92, "errors": [], "severity": "NONE", '
            '"suggestions": [], "refined_plan": "SKIP", '
            '"improvements": [], "reuse_pattern": "", "knowledge_atom": ""}'
        )
        agent.llm = MagicMock()
        agent.llm.ainvoke = AsyncMock(return_value=llm_response)

        result = await agent.agents_reflector_critique("## Plan", "ctx", "task")

        required_keys = {
            "confidence",
            "errors",
            "severity",
            "suggestions",
            "refined_plan",
            "improvements",
            "reuse_pattern",
            "knowledge_atom",
        }
        assert required_keys.issubset(result.keys())
