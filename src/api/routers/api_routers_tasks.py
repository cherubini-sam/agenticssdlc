"""POST /api/v1/task: runs the full 6-phase SDLC workflow and returns the result inline."""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, HTTPException, Request

from src.api.api_utils import (
    API_ROUTERS_AGENTS_MANAGER,
    API_ROUTERS_AGENTS_STATUS_ERROR,
    API_ROUTERS_AGENTS_STATUS_SUCCESS,
    API_ROUTERS_TASKS_LOG_FAILED,
    API_ROUTERS_TASKS_NOT_FOUND,
    API_ROUTERS_TASKS_STATUS_COMPLETED,
    API_ROUTERS_TASKS_STATUS_FAILED,
)
from src.api.middleware.api_middleware_observability import ACTIVE_WORKFLOWS, record_metrics
from src.api.schemas.api_schemas_task import ApiSchemasTaskRequest, ApiSchemasTaskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.post("/task", response_model=ApiSchemasTaskResponse)
async def api_routers_create_task(
    task_request: ApiSchemasTaskRequest, request: Request
) -> ApiSchemasTaskResponse:
    """Execute the full agent pipeline and return the result inline."""

    ACTIVE_WORKFLOWS.inc()
    start = time.perf_counter()

    try:
        response: ApiSchemasTaskResponse = await request.app.state.manager.agents_manager_run(
            task_request
        )
        response.latency_ms = (time.perf_counter() - start) * 1000

        bq_status = (
            API_ROUTERS_AGENTS_STATUS_SUCCESS
            if response.status == API_ROUTERS_TASKS_STATUS_COMPLETED
            else API_ROUTERS_AGENTS_STATUS_ERROR
        )
        phases = sorted(int(p) for p in response.phases_completed)
        phase_reached = phases[-1] if phases else 0

        record_metrics(
            agent=API_ROUTERS_AGENTS_MANAGER,
            phase=str(phase_reached),
            status=bq_status,
            latency_s=response.latency_ms / 1000,
            confidence=response.confidence,
        )

        # Fire-and-forget audit writes so we don't block the response
        audit_logger = getattr(request.app.state, "audit_logger", None)
        if audit_logger:
            asyncio.create_task(
                audit_logger.analytics_bigquery_log_agent_call(
                    session_id=task_request.task_id,
                    agent_name=API_ROUTERS_AGENTS_MANAGER,
                    phase=phase_reached,
                    latency_ms=response.latency_ms,
                    confidence=response.confidence,
                    status=bq_status,
                    task_content=task_request.content,
                    error=response.error,
                )
            )

        supabase_logger = getattr(request.app.state, "supabase_logger", None)
        if supabase_logger and supabase_logger.is_enabled:
            final_status = (
                API_ROUTERS_TASKS_STATUS_COMPLETED
                if response.status == API_ROUTERS_TASKS_STATUS_COMPLETED
                else API_ROUTERS_TASKS_STATUS_FAILED
            )
            asyncio.create_task(
                supabase_logger.analytics_supabase_log_agent_call(
                    session_id=task_request.task_id,
                    agent_name=API_ROUTERS_AGENTS_MANAGER,
                    phase=phase_reached,
                    latency_ms=response.latency_ms,
                    confidence=response.confidence,
                    status=bq_status,
                    task_content=task_request.content,
                    error=response.error,
                )
            )
            asyncio.create_task(
                supabase_logger.analytics_supabase_upsert_workflow_snapshot(
                    session_id=task_request.task_id,
                    phase_reached=phase_reached,
                    retry_count=0,
                    final_status=final_status,
                    confidence=response.confidence,
                    latency_ms=response.latency_ms,
                    snapshot_data={
                        "phases_completed": [int(p) for p in response.phases_completed],
                        "agent_trace": response.agent_trace,
                        "error_code": response.error_code.value if response.error_code else None,
                    },
                )
            )

        return response

    except Exception as exc:
        logger.error(
            API_ROUTERS_TASKS_LOG_FAILED.format(task_id=task_request.task_id, error=exc),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        ACTIVE_WORKFLOWS.dec()


@router.get("/task/{task_id}")
async def api_routers_get_task(task_id: str) -> dict:
    """Placeholder: v1 is stateless, so there's nothing to look up here."""

    raise HTTPException(
        status_code=404,
        detail=API_ROUTERS_TASKS_NOT_FOUND.format(task_id=task_id),
    )
