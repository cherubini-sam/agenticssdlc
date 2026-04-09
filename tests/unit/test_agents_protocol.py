"""AgentsProtocol Phase 1 boot validation (task_id, content length, etc.)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.agents_protocol import AgentsProtocol


class TestAgentsProtocolValidate:
    """Tests for the async agents_protocol_validate entrypoint."""

    @pytest.mark.asyncio
    async def test_valid_input_returns_green(self) -> None:
        """Valid task_id and content produce system_green with no violations."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(
            task_id="task-001", content="Build a REST API"
        )

        assert result["protocol_status"] == "system_green"
        assert result["violations"] == []
        assert result["boot_agent"] == "PROTOCOL"
        assert result["boot_phase"] == 0

    @pytest.mark.asyncio
    async def test_empty_task_id_returns_violation(self) -> None:
        """Empty task_id yields system_error with a task_id violation."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="", content="Some content")

        assert result["protocol_status"] == "system_error"
        assert len(result["violations"]) >= 1
        assert any("task_id" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_whitespace_task_id_returns_violation(self) -> None:
        """Whitespace-only task_id yields a task_id violation."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="   ", content="Some content")

        assert result["protocol_status"] == "system_error"
        assert any("task_id" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_empty_content_returns_violation(self) -> None:
        """Empty content yields a content violation."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="task-001", content="")

        assert result["protocol_status"] == "system_error"
        assert any("content" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_whitespace_content_returns_violation(self) -> None:
        """Whitespace-only content yields a content violation."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="task-001", content="   ")

        assert result["protocol_status"] == "system_error"
        assert any("content" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_content_exceeds_max_length_returns_violation(self) -> None:
        """Content beyond 4096 characters yields a length violation."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        long_content = "x" * 5000  # well past the 4096 cap

        result = await agent.agents_protocol_validate(task_id="task-001", content=long_content)

        assert result["protocol_status"] == "system_error"
        assert any("4096" in v or "exceeds" in v.lower() for v in result["violations"])

    @pytest.mark.asyncio
    async def test_content_at_max_length_is_valid(self) -> None:
        """Content of exactly 4096 characters passes validation."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        max_content = "a" * 4096

        result = await agent.agents_protocol_validate(task_id="task-001", content=max_content)

        assert result["protocol_status"] == "system_green"

    @pytest.mark.asyncio
    async def test_multiple_violations_accumulated(self) -> None:
        """Both empty task_id and empty content produce at least two violations."""

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="", content="")

        assert result["protocol_status"] == "system_error"
        assert len(result["violations"]) >= 2


class TestAgentsProtocolCheckIntegrity:
    """Tests for the synchronous _agents_protocol_check_integrity helper."""

    def test_valid_inputs_no_violations(self) -> None:
        """Valid task_id and content return an empty violations list."""

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("task-1", "Do something useful")

        assert violations == []

    def test_empty_task_id_violation(self) -> None:
        """Empty task_id produces exactly one task_id violation."""

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("", "Some content")

        assert len(violations) == 1
        assert "task_id" in violations[0]

    def test_empty_content_violation(self) -> None:
        """Empty content produces exactly one content violation."""

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("task-1", "")

        assert len(violations) == 1
        assert "content" in violations[0]

    def test_oversized_content_violation(self) -> None:
        """Content over 4096 chars produces a violation mentioning '4096'."""

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("task-1", "x" * 4097)

        assert len(violations) == 1
        assert "4096" in violations[0]

    def test_both_empty_returns_two_violations(self) -> None:
        """Both empty task_id and content produce exactly two violations."""

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("", "")

        assert len(violations) == 2
