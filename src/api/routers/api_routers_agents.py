"""GET /api/v1/agents/status: returns a snapshot of the agent roster and system metadata."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

from src.api.api_utils import (
    API_AGENT_LIBRARIAN_MODEL,
    API_AGENT_STATUS_ACTIVE,
    API_AGENT_STATUS_IDLE,
    API_APP_VERSION,
    API_ROUTERS_AGENTS_ARCHITECT,
    API_ROUTERS_AGENTS_ENGINEER,
    API_ROUTERS_AGENTS_LIBRARIAN,
    API_ROUTERS_AGENTS_MANAGER,
    API_ROUTERS_AGENTS_REFLECTOR,
    API_ROUTERS_AGENTS_VALIDATOR,
)
from src.api.middleware.api_middleware_observability import get_active_workflow_count
from src.api.schemas.api_schemas_agents import ApiSchemasAgentStatus, ApiSchemasSystemStatus
from src.core.core_config import core_config_get_settings as get_settings
from src.core.core_utils import CORE_LLM_AGENT_TIER_MAP, CORE_LLM_TIER_HIGH


def _model_for(agent_name: str, settings) -> str:
    tier = CORE_LLM_AGENT_TIER_MAP.get(agent_name)
    if tier == CORE_LLM_TIER_HIGH:
        return settings.gemini_model_high
    return settings.gemini_model_low


router = APIRouter(prefix="/api/v1", tags=["agents"])


@router.get("/agents/status", response_model=ApiSchemasSystemStatus)
async def api_routers_agents_status(request: Request) -> ApiSchemasSystemStatus:
    """Return current agent roster, uptime, and vector store backend.

    Args:
        request: Starlette request providing access to app.state.vector_store
            and app.state.start_time, set during application lifespan startup.

    Returns:
        ApiSchemasSystemStatus with version, uptime_s, vector_store backend
        name, and a 6-agent roster with current active/idle status.
    """

    settings = get_settings()

    # Manager is "active" when workflows are in-flight, otherwise "idle"
    manager_status = (
        API_AGENT_STATUS_ACTIVE if get_active_workflow_count() > 0 else API_AGENT_STATUS_IDLE
    )
    agents = [
        ApiSchemasAgentStatus(
            name=API_ROUTERS_AGENTS_MANAGER,
            model=_model_for(API_ROUTERS_AGENTS_MANAGER, settings),
            status=manager_status,
        ),
        ApiSchemasAgentStatus(
            name=API_ROUTERS_AGENTS_ARCHITECT,
            model=_model_for(API_ROUTERS_AGENTS_ARCHITECT, settings),
            status=API_AGENT_STATUS_IDLE,
        ),
        ApiSchemasAgentStatus(
            name=API_ROUTERS_AGENTS_ENGINEER,
            model=_model_for(API_ROUTERS_AGENTS_ENGINEER, settings),
            status=API_AGENT_STATUS_IDLE,
        ),
        ApiSchemasAgentStatus(
            name=API_ROUTERS_AGENTS_VALIDATOR,
            model=_model_for(API_ROUTERS_AGENTS_VALIDATOR, settings),
            status=API_AGENT_STATUS_IDLE,
        ),
        ApiSchemasAgentStatus(
            name=API_ROUTERS_AGENTS_LIBRARIAN,
            model=API_AGENT_LIBRARIAN_MODEL,
            status=API_AGENT_STATUS_IDLE,
        ),
        ApiSchemasAgentStatus(
            name=API_ROUTERS_AGENTS_REFLECTOR,
            model=_model_for(API_ROUTERS_AGENTS_REFLECTOR, settings),
            status=API_AGENT_STATUS_IDLE,
        ),
    ]

    vector_store = getattr(request.app.state, "vector_store", None)
    vs_primary = getattr(vector_store, "primary", "unknown") if vector_store else "not_initialized"

    start_time = getattr(request.app.state, "start_time", time.time())

    return ApiSchemasSystemStatus(
        version=API_APP_VERSION,
        uptime_s=time.time() - start_time,
        vector_store=vs_primary,
        agents=agents,
    )
