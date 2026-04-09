"""API Pydantic schemas validation, defaults, serialization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.api_schemas_agents import ApiSchemasAgentStatus, ApiSchemasSystemStatus
from api.schemas.api_schemas_task import (
    ApiSchemasTaskRequest,
    ApiSchemasTaskResponse,
    ApiSchemasWorkflowPhase,
)


class TestWorkflowPhase:
    """Tests for ApiSchemasWorkflowPhase enum values."""

    def test_phases_defined(self) -> None:
        """Each workflow phase has the expected integer value."""

        assert ApiSchemasWorkflowPhase.TASK == 1
        assert ApiSchemasWorkflowPhase.CONTEXT == 2
        assert ApiSchemasWorkflowPhase.PLAN == 3
        assert ApiSchemasWorkflowPhase.CRITIQUE == 4
        assert ApiSchemasWorkflowPhase.EXECUTE == 5
        assert ApiSchemasWorkflowPhase.VERIFY == 6


class TestTaskRequest:
    """Tests for ApiSchemasTaskRequest validation and defaults."""

    def test_valid_request(self) -> None:
        """Valid content is stored as-is."""

        req = ApiSchemasTaskRequest(content="What is the capital of France?")
        assert req.content == "What is the capital of France?"

    def test_content_stripped(self) -> None:
        """Leading and trailing whitespace is stripped from content."""

        req = ApiSchemasTaskRequest(content="  hello world  ")
        assert req.content == "hello world"

    def test_empty_content_raises(self) -> None:
        """Empty content raises a ValidationError."""

        with pytest.raises(ValidationError):
            ApiSchemasTaskRequest(content="")

    def test_whitespace_only_raises(self) -> None:
        """Whitespace-only content raises a ValidationError."""

        with pytest.raises(ValidationError):
            ApiSchemasTaskRequest(content="   ")

    def test_max_length(self) -> None:
        """Content of exactly 4096 characters is accepted."""

        req = ApiSchemasTaskRequest(content="x" * 4096)
        assert len(req.content) == 4096

    def test_exceeds_max_length_raises(self) -> None:
        """Content longer than 4096 characters raises a ValidationError."""

        with pytest.raises(ValidationError):
            ApiSchemasTaskRequest(content="x" * 4097)

    def test_task_id_auto_generated(self) -> None:
        """task_id is auto-generated as a non-empty string."""

        req = ApiSchemasTaskRequest(content="hello")
        assert req.task_id
        assert len(req.task_id) > 0

    def test_default_priority(self) -> None:
        """Default priority is 'normal'."""

        req = ApiSchemasTaskRequest(content="hello")
        assert req.priority == "normal"


class TestTaskResponse:
    """Tests for ApiSchemasTaskResponse validation and serialisation."""

    def test_valid_response(self) -> None:
        """Valid response fields are stored and accessible."""

        resp = ApiSchemasTaskResponse(
            task_id="test-123",
            status="completed",
            result="Paris",
            phases_completed=[
                ApiSchemasWorkflowPhase.TASK,
                ApiSchemasWorkflowPhase.CONTEXT,
                ApiSchemasWorkflowPhase.VERIFY,
            ],
            confidence=0.95,
            latency_ms=1200.5,
            agent_trace=[{"agent": "ARCHITECT"}, {"agent": "ENGINEER"}],
        )
        assert resp.status == "completed"
        assert resp.confidence == 0.95
        assert len(resp.phases_completed) == 3

    def test_serialization(self) -> None:
        """model_dump produces a plain dict with the expected field values."""

        resp = ApiSchemasTaskResponse(
            task_id="test-456",
            status="failed",
            result=None,
            phases_completed=[ApiSchemasWorkflowPhase.TASK],
            confidence=0.0,
            latency_ms=500.0,
            agent_trace=[],
        )
        data = resp.model_dump()
        assert data["status"] == "failed"
        assert isinstance(data["agent_trace"], list)

    def test_status_must_be_valid_literal(self) -> None:
        """Status values outside the allowed Literal raise a ValidationError."""

        with pytest.raises(ValidationError):
            ApiSchemasTaskResponse(
                task_id="x",
                status="success",  # not in the Literal -- must be "completed" or "failed"
                result=None,
                phases_completed=[],
                confidence=0.0,
                latency_ms=0.0,
                agent_trace=[],
            )


class TestAgentStatus:
    """Tests for ApiSchemasAgentStatus field assignment."""

    def test_agent_status_fields(self) -> None:
        """Fields are stored correctly and last_invoked defaults to None."""

        status = ApiSchemasAgentStatus(
            name="ARCHITECT",
            status="active",
            model="gemini-2.5-flash",
        )
        assert status.name == "ARCHITECT"
        assert status.status == "active"
        assert status.last_invoked is None


class TestSystemStatus:
    """Tests for ApiSchemasSystemStatus aggregation."""

    def test_system_status(self) -> None:
        """System status aggregates all agents and stores vector_store name."""

        agents = [
            ApiSchemasAgentStatus(
                name=name,
                status="active",
                model="gemini-2.5-flash",
            )
            for name in [
                "MANAGER",
                "ARCHITECT",
                "ENGINEER",
                "VALIDATOR",
                "LIBRARIAN",
                "REFLECTOR",
            ]
        ]
        sys_status = ApiSchemasSystemStatus(
            version="3.1.0",
            uptime_s=42.5,
            vector_store="chroma",
            agents=agents,
        )
        assert len(sys_status.agents) == 6
        assert sys_status.vector_store == "chroma"
