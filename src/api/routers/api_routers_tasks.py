"""POST /api/v1/task: runs the full 6-phase SDLC workflow and returns the result inline."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from src.api.api_utils import (
    API_HTTP_501_NOT_IMPLEMENTED,
    API_MS_PER_SECOND,
    API_ROUTERS_AGENTS_MANAGER,
    API_ROUTERS_AGENTS_STATUS_ERROR,
    API_ROUTERS_AGENTS_STATUS_SUCCESS,
    API_ROUTERS_TASKS_INTERNAL_ERROR,
    API_ROUTERS_TASKS_LOG_AUDIT_FAILED,
    API_ROUTERS_TASKS_LOG_FAILED,
    API_ROUTERS_TASKS_NOT_FOUND,
    API_ROUTERS_TASKS_STATUS_COMPLETED,
    API_ROUTERS_TASKS_STATUS_FAILED,
)
from src.api.middleware.api_middleware_observability import ACTIVE_WORKFLOWS, record_metrics
from src.api.schemas.api_schemas_task import (
    ApiSchemasErrorCode,
    ApiSchemasTaskRequest,
    ApiSchemasTaskResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["tasks"])


async def api_routers_audit(coro, task_id: str) -> None:
    """Wrap a fire-and-forget audit coroutine so failures are logged instead of silently dropped."""

    try:
        await coro
    except Exception as exc:
        logger.error(API_ROUTERS_TASKS_LOG_AUDIT_FAILED, task_id, exc, exc_info=True)


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
        response.latency_ms = (time.perf_counter() - start) * API_MS_PER_SECOND

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
            latency_s=response.latency_ms / API_MS_PER_SECOND,
            confidence=response.confidence,
        )

        # Fire-and-forget audit writes so we don't block the response
        audit_logger = getattr(request.app.state, "audit_logger", None)
        if audit_logger:
            asyncio.create_task(
                api_routers_audit(
                    audit_logger.analytics_bigquery_log_agent_call(
                        session_id=task_request.task_id,
                        agent_name=API_ROUTERS_AGENTS_MANAGER,
                        phase=phase_reached,
                        latency_ms=response.latency_ms,
                        confidence=response.confidence,
                        status=bq_status,
                        task_content=task_request.content,
                        error=response.error,
                    ),
                    task_request.task_id,
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
                api_routers_audit(
                    supabase_logger.analytics_supabase_log_agent_call(
                        session_id=task_request.task_id,
                        agent_name=API_ROUTERS_AGENTS_MANAGER,
                        phase=phase_reached,
                        latency_ms=response.latency_ms,
                        confidence=response.confidence,
                        status=bq_status,
                        task_content=task_request.content,
                        error=response.error,
                    ),
                    task_request.task_id,
                )
            )
            asyncio.create_task(
                api_routers_audit(
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
                            "error_code": (
                                response.error_code.value if response.error_code else None
                            ),
                        },
                    ),
                    task_request.task_id,
                )
            )

        return response

    except Exception as exc:
        logger.error(
            API_ROUTERS_TASKS_LOG_FAILED.format(task_id=task_request.task_id, error=exc),
            exc_info=True,
        )
        latency_ms = (time.perf_counter() - start) * API_MS_PER_SECOND
        return ApiSchemasTaskResponse(
            task_id=task_request.task_id,
            status=API_ROUTERS_TASKS_STATUS_FAILED,
            result=None,
            phases_completed=[],
            confidence=0.0,
            latency_ms=latency_ms,
            agent_trace=[],
            error=API_ROUTERS_TASKS_INTERNAL_ERROR,
            error_code=ApiSchemasErrorCode.INTERNAL_ERROR,
            created_at=datetime.now(timezone.utc),
        )
    finally:
        ACTIVE_WORKFLOWS.dec()


@router.get("/task/{task_id}")
async def api_routers_get_task(task_id: str) -> dict:
    """Not implemented: v1 is stateless — results are returned synchronously on POST."""

    raise HTTPException(
        status_code=API_HTTP_501_NOT_IMPLEMENTED,
        detail=API_ROUTERS_TASKS_NOT_FOUND.format(task_id=task_id),
    )
