"""API key + Basic Auth middleware."""

from __future__ import annotations

import base64
import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.api.api_utils import API_MIDDLEWARE_AUTH_METRICS_PATHS, API_MIDDLEWARE_AUTH_OPEN_PATHS
from src.core.core_config import core_config_get_settings as get_settings

logger = logging.getLogger(__name__)

OPEN_PATHS: frozenset[str] = API_MIDDLEWARE_AUTH_OPEN_PATHS
METRICS_PATHS: frozenset[str] = API_MIDDLEWARE_AUTH_METRICS_PATHS


class ApiMiddlewareApiKey(BaseHTTPMiddleware):
    """
    Three-tier auth:
    1. Open paths (health, docs): no credentials needed.
    2. /metrics: Basic Auth when creds are configured, open otherwise.
    3. Everything else: X-API-Key header required (unless the key isn't set,
    which means we're in local dev mode).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()

        if request.url.path in METRICS_PATHS:
            if settings.metrics_username and settings.metrics_password:
                return await self._check_basic_auth(request, call_next, settings)
            return await call_next(request)

        if request.url.path in OPEN_PATHS:
            return await call_next(request)

        # No key configured; let everything through (local dev / first-run)
        if not settings.agentics_sdlc_api_key:
            logger.debug("Auth disabled: AGENTICS_SDLC_API_KEY not set")
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")

        if not api_key:
            logger.warning(f"Unauthenticated request: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "X-API-Key header is required",
                    "hint": "Add header: X-API-Key: <your-key>",
                },
            )

        if api_key != settings.agentics_sdlc_api_key:
            logger.warning(
                f"Invalid API key attempt: {request.method} {request.url.path} "
                f"key_prefix={api_key[:6]}..."
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key"},
            )

        return await call_next(request)

    @staticmethod
    async def _check_basic_auth(
        request: Request,
        call_next: RequestResponseEndpoint,
        settings,  # type: ignore[type-arg]
    ) -> Response:
        """Validate HTTP Basic Auth for /metrics (used by Grafana scrape jobs)."""

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="metrics"'},
                content="Unauthorized",
            )
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, _, password = decoded.partition(":")
        except Exception:
            return Response(status_code=401, content="Unauthorized")

        if username != settings.metrics_username or password != settings.metrics_password:
            logger.warning("Invalid Basic Auth attempt on /metrics")
            return Response(status_code=403, content="Forbidden")

        return await call_next(request)
