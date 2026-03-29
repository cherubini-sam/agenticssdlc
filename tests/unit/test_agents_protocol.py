"""AgentsProtocol Phase 1 boot validation (task_id, content length, etc.)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestAgentsProtocolValidate:

    @pytest.mark.asyncio
    async def test_valid_input_returns_green(self) -> None:
        from agents.agents_protocol import AgentsProtocol

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
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="", content="Some content")

        assert result["protocol_status"] == "system_error"
        assert len(result["violations"]) >= 1
        assert any("task_id" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_whitespace_task_id_returns_violation(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="   ", content="Some content")

        assert result["protocol_status"] == "system_error"
        assert any("task_id" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_empty_content_returns_violation(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="task-001", content="")

        assert result["protocol_status"] == "system_error"
        assert any("content" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_whitespace_content_returns_violation(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="task-001", content="   ")

        assert result["protocol_status"] == "system_error"
        assert any("content" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_content_exceeds_max_length_returns_violation(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        long_content = "x" * 5000  # well past the 4096 cap

        result = await agent.agents_protocol_validate(task_id="task-001", content=long_content)

        assert result["protocol_status"] == "system_error"
        assert any("4096" in v or "exceeds" in v.lower() for v in result["violations"])

    @pytest.mark.asyncio
    async def test_content_at_max_length_is_valid(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        max_content = "a" * 4096

        result = await agent.agents_protocol_validate(task_id="task-001", content=max_content)

        assert result["protocol_status"] == "system_green"

    @pytest.mark.asyncio
    async def test_multiple_violations_accumulated(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        agent.logger = MagicMock()

        result = await agent.agents_protocol_validate(task_id="", content="")

        assert result["protocol_status"] == "system_error"
        assert len(result["violations"]) >= 2


class TestAgentsProtocolCheckIntegrity:

    def test_valid_inputs_no_violations(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("task-1", "Do something useful")

        assert violations == []

    def test_empty_task_id_violation(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("", "Some content")

        assert len(violations) == 1
        assert "task_id" in violations[0]

    def test_empty_content_violation(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("task-1", "")

        assert len(violations) == 1
        assert "content" in violations[0]

    def test_oversized_content_violation(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("task-1", "x" * 4097)

        assert len(violations) == 1
        assert "4096" in violations[0]

    def test_both_empty_returns_two_violations(self) -> None:
        from agents.agents_protocol import AgentsProtocol

        agent = AgentsProtocol()
        violations = agent._agents_protocol_check_integrity("", "")

        assert len(violations) == 2
