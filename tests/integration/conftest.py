"""Shared fixtures for integration tests mock manager, vector store, and HTTP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.schemas.api_schemas_task import ApiSchemasTaskResponse as TaskResponse


@pytest.fixture
def mock_manager():
    manager = MagicMock()
    manager.run = AsyncMock(
        return_value=TaskResponse(
            task_id="test-task-id",
            status="completed",
            result="Test result",
            phases_completed=[],
            confidence=0.92,
            latency_ms=1500.0,
            agent_trace=[
                {"agent": "PROTOCOL"},
                {"agent": "MANAGER"},
                {"agent": "LIBRARIAN"},
                {"agent": "ARCHITECT"},
                {"agent": "REFLECTOR"},
                {"agent": "ENGINEER"},
                {"agent": "VALIDATOR"},
            ],
        )
    )
    return manager


@pytest.fixture
def mock_vector_store():
    vs = MagicMock()
    vs.primary = "chroma"
    return vs


@pytest.fixture
def client(mock_manager, mock_vector_store):
    """Fully patched TestClient -- no real LLM calls, no real vector store."""
    with (
        patch(
            "agents.agents_manager.AgentsManager.agents_manager_create",
            new_callable=AsyncMock,
            return_value=mock_manager,
        ),
        patch(
            "rag.rag_vector_store.RagVectorStore.rag_vector_store_create",
            new_callable=AsyncMock,
            return_value=mock_vector_store,
        ),
        patch("core.core_config.core_config_validate_settings"),
        patch.dict(
            "os.environ",
            {"AGENTICS_SDLC_API_KEY": "test-key-123", "GCP_PROJECT_ID": "test-project"},
        ),
    ):
        import core.core_config as _cfg

        _cfg.core_config_get_settings.cache_clear()
        from api.main import app

        with TestClient(app) as c:
            yield c
        _cfg.core_config_get_settings.cache_clear()
