"""Health, readiness, and liveness probes. No auth required."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.api.api_utils import (
    API_HEALTH_KEY_CHECKS,
    API_HEALTH_KEY_SERVICE,
    API_HEALTH_KEY_STATUS,
    API_HEALTH_KEY_TIMESTAMP,
    API_HEALTH_KEY_VERSION,
    API_HEALTH_STATUS_ALIVE,
    API_HEALTH_STATUS_HEALTHY,
    API_HEALTH_STATUS_NOT_READY,
    API_HEALTH_STATUS_READY,
    API_HEALTH_VAL_NOT_INIT,
    API_HEALTH_VAL_OK,
    API_HTTP_200_OK,
    API_HTTP_503_SERVICE_UNAVAILABLE,
    API_SERVICE_NAME,
    API_SERVICE_VERSION,
)

router = APIRouter(tags=["health"])


@router.get("/health")
async def api_routers_health() -> dict:
    """Shallow check: if the process is up, this returns 200."""

    return {
        API_HEALTH_KEY_STATUS: API_HEALTH_STATUS_HEALTHY,
        API_HEALTH_KEY_SERVICE: API_SERVICE_NAME,
        API_HEALTH_KEY_VERSION: API_SERVICE_VERSION,
    }


@router.get("/readiness")
async def api_routers_readiness(request: Request) -> JSONResponse:
    """Deep check: 503 until both the agent manager and vector store are live."""

    checks: dict[str, str] = {}
    all_ready = True

    manager = getattr(request.app.state, "manager", None)
    checks["manager"] = API_HEALTH_VAL_OK if manager is not None else API_HEALTH_VAL_NOT_INIT
    if manager is None:
        all_ready = False

    vector_store = getattr(request.app.state, "vector_store", None)
    checks["vector_store"] = (
        API_HEALTH_VAL_OK if vector_store is not None else API_HEALTH_VAL_NOT_INIT
    )
    if vector_store is None:
        all_ready = False

    status_code = API_HTTP_200_OK if all_ready else API_HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            API_HEALTH_KEY_STATUS: (
                API_HEALTH_STATUS_READY if all_ready else API_HEALTH_STATUS_NOT_READY
            ),
            API_HEALTH_KEY_CHECKS: checks,
        },
    )


@router.get("/liveness")
async def api_routers_liveness() -> dict:
    """K8s liveness probe: just proves the event loop isn't stuck."""

    return {
        API_HEALTH_KEY_STATUS: API_HEALTH_STATUS_ALIVE,
        API_HEALTH_KEY_TIMESTAMP: datetime.now(timezone.utc).isoformat(),
    }
