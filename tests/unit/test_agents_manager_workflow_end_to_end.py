"""End-to-end LangGraph drive with canned agents — happy path and refusal path."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.agents_manager import AgentsManager
from agents.agents_utils import (
    AGENTS_REFUSAL_STATUS_PREFIX,
    AGENTS_TRACE_ACTION_EXECUTION_COMPLETE,
    AGENTS_TRACE_ACTION_EXECUTION_REFUSED,
)
from api.schemas.api_schemas_task import ApiSchemasErrorCode, ApiSchemasTaskRequest


@pytest.mark.asyncio
class TestWorkflowHappyPath:
    """Full graph with canned agents produces a completed response with a trace."""

    async def test_happy_path_returns_completed_with_trace(self) -> None:
        """Sunny-day workflow: protocol green, plan drafted, approved, executed, verified."""

        with (
            patch("agents.agents_manager.AgentsProtocol") as mock_proto,
            patch("agents.agents_manager.AgentsLibrarian") as mock_lib,
            patch("agents.agents_manager.AgentsArchitect") as mock_arch,
            patch("agents.agents_manager.AgentsReflector") as mock_refl,
            patch("agents.agents_manager.AgentsEngineer") as mock_eng,
            patch("agents.agents_manager.AgentsValidator") as mock_val,
            patch("agents.agents_manager.StorageGcs") as mock_gcs,
        ):

            mock_proto.return_value.agents_protocol_validate = AsyncMock(
                return_value={"protocol_status": "system_green", "violations": []}
            )
            mock_lib.return_value.agents_librarian_retrieve = AsyncMock(return_value=[])
            mock_arch.return_value.agents_architect_draft_plan = AsyncMock(
                return_value="## Plan\n1. Implement feature.\n2. Test feature."
            )
            mock_refl.return_value.agents_reflector_critique = AsyncMock(
                return_value={
                    "errors": [],
                    "severity": "NONE",
                    "suggestions": [],
                    "confidence": 0.95,
                    "refined_plan": "",
                    "improvements": [],
                    "reuse_pattern": "",
                    "knowledge_atom": "",
                    "approved": True,
                }
            )
            mock_eng.return_value.agents_engineer_execute = AsyncMock(
                return_value="def feature():\n    return 42"
            )
            mock_val.return_value.agents_validator_verify = AsyncMock(
                return_value={"verdict": "passed", "score": 0.95, "issues": [], "error": None}
            )
            mock_gcs.return_value.storage_gcs_upload_artifact = MagicMock(
                return_value="gs://bucket/artifact"
            )

            manager = await AgentsManager.agents_manager_create()
            request = ApiSchemasTaskRequest(task_id="happy-001", content="Build a feature.")
            response = await manager.agents_manager_run(request)

        assert response.status == "completed"
        assert response.result == "def feature():\n    return 42"
        assert response.error is None
        actions = [m.get("action") for m in response.agent_trace if "action" in m]
        assert AGENTS_TRACE_ACTION_EXECUTION_COMPLETE in actions
        assert AGENTS_TRACE_ACTION_EXECUTION_REFUSED not in actions


@pytest.mark.asyncio
class TestWorkflowRefusalPath:
    """Refusal at EXECUTE must surface as status=failed, never completed+passed."""

    async def test_engineer_refusal_surfaces_as_failed(self) -> None:
        """ENGINEER emits context_missing → MANAGER sets error, skips VALIDATOR, returns failed."""

        refusal = (
            f"{AGENTS_REFUSAL_STATUS_PREFIX}\n"
            "missing_sections: INTEGRATION & BENCHMARK AUTHORITY, FEEDBACK LOOP\n"
            "The ENGINEER refused to execute."
        )

        with (
            patch("agents.agents_manager.AgentsProtocol") as mock_proto,
            patch("agents.agents_manager.AgentsLibrarian") as mock_lib,
            patch("agents.agents_manager.AgentsArchitect") as mock_arch,
            patch("agents.agents_manager.AgentsReflector") as mock_refl,
            patch("agents.agents_manager.AgentsEngineer") as mock_eng,
            patch("agents.agents_manager.AgentsValidator") as mock_val,
            patch("agents.agents_manager.StorageGcs") as mock_gcs,
        ):

            mock_proto.return_value.agents_protocol_validate = AsyncMock(
                return_value={"protocol_status": "system_green", "violations": []}
            )
            mock_lib.return_value.agents_librarian_retrieve = AsyncMock(return_value=[])
            mock_arch.return_value.agents_architect_draft_plan = AsyncMock(
                return_value="## Plan\n1. Consume INTEGRATION & BENCHMARK AUTHORITY."
            )
            mock_refl.return_value.agents_reflector_critique = AsyncMock(
                return_value={
                    "errors": [],
                    "severity": "NONE",
                    "suggestions": [],
                    "confidence": 0.95,
                    "refined_plan": "",
                    "improvements": [],
                    "reuse_pattern": "",
                    "knowledge_atom": "",
                    "approved": True,
                }
            )
            mock_eng.return_value.agents_engineer_execute = AsyncMock(return_value=refusal)
            mock_val.return_value.agents_validator_verify = AsyncMock()
            mock_gcs.return_value.storage_gcs_upload_artifact = MagicMock(
                return_value="gs://bucket/artifact"
            )

            manager = await AgentsManager.agents_manager_create()
            request = ApiSchemasTaskRequest(task_id="refusal-001", content="Build a feature.")
            response = await manager.agents_manager_run(request)

        assert response.status == "failed"
        assert response.error is not None
        assert response.error_code == ApiSchemasErrorCode.AGENT_EXECUTION_REFUSED
        actions = [m.get("action") for m in response.agent_trace if "action" in m]
        assert AGENTS_TRACE_ACTION_EXECUTION_REFUSED in actions
        assert AGENTS_TRACE_ACTION_EXECUTION_COMPLETE not in actions
        mock_val.return_value.agents_validator_verify.assert_not_called()
