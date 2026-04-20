"""API key + Basic Auth middleware."""

from __future__ import annotations

import base64
import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.api.api_utils import (
    API_HEADER_API_KEY,
    API_HTTP_401_UNAUTHORIZED,
    API_HTTP_403_FORBIDDEN,
    API_MIDDLEWARE_AUTH_BASIC_REALM,
    API_MIDDLEWARE_AUTH_FORBIDDEN,
    API_MIDDLEWARE_AUTH_INVALID_KEY_DETAIL,
    API_MIDDLEWARE_AUTH_LOG_DISABLED,
    API_MIDDLEWARE_AUTH_LOG_INVALID_BASIC,
    API_MIDDLEWARE_AUTH_LOG_INVALID_KEY,
    API_MIDDLEWARE_AUTH_LOG_UNAUTHENTICATED,
    API_MIDDLEWARE_AUTH_METRICS_PATHS,
    API_MIDDLEWARE_AUTH_MISSING_KEY_DETAIL,
    API_MIDDLEWARE_AUTH_MISSING_KEY_HINT,
    API_MIDDLEWARE_AUTH_OPEN_PATHS,
    API_MIDDLEWARE_AUTH_UNAUTHORIZED,
)
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
        """Enforce API key or Basic Auth depending on the requested path.

        Args:
            request: Starlette request.
            call_next: Next middleware.

        Returns:
            401 if key missing, 403 if key invalid, otherwise next middleware
            response.
        """
        settings = get_settings()

        if request.url.path in METRICS_PATHS:
            if settings.metrics_username and settings.metrics_password:
                return await self._check_basic_auth(request, call_next, settings)
            return await call_next(request)

        if request.url.path in OPEN_PATHS:
            return await call_next(request)

        # No key configured; let everything through (local dev / first-run)
        if not settings.agentics_sdlc_api_key:
            logger.debug(API_MIDDLEWARE_AUTH_LOG_DISABLED)
            return await call_next(request)

        api_key = request.headers.get(API_HEADER_API_KEY, "")

        if not api_key:
            logger.warning(
                API_MIDDLEWARE_AUTH_LOG_UNAUTHENTICATED, request.method, request.url.path
            )
            return JSONResponse(
                status_code=API_HTTP_401_UNAUTHORIZED,
                content={
                    "detail": API_MIDDLEWARE_AUTH_MISSING_KEY_DETAIL,
                    "hint": API_MIDDLEWARE_AUTH_MISSING_KEY_HINT,
                },
            )

        if api_key != settings.agentics_sdlc_api_key:
            logger.warning(
                API_MIDDLEWARE_AUTH_LOG_INVALID_KEY,
                request.method,
                request.url.path,
                api_key[:6],
            )
            return JSONResponse(
                status_code=API_HTTP_403_FORBIDDEN,
                content={"detail": API_MIDDLEWARE_AUTH_INVALID_KEY_DETAIL},
            )

        return await call_next(request)

    @staticmethod
    async def _check_basic_auth(
        request: Request,
        call_next: RequestResponseEndpoint,
        settings,  # type: ignore[type-arg]
    ) -> Response:
        """Validate HTTP Basic Auth for /metrics (used by Grafana scrape jobs).

        Args:
            request: Starlette request with Authorization header.
            call_next: Next handler.
            settings: CoreSettings with metrics_username and metrics_password.

        Returns:
            401 if Authorization header absent or malformed, 403 if credentials
            do not match, otherwise next middleware response.
        """

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return Response(
                status_code=API_HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": API_MIDDLEWARE_AUTH_BASIC_REALM},
                content=API_MIDDLEWARE_AUTH_UNAUTHORIZED,
            )
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, _, password = decoded.partition(":")
        except Exception:
            return Response(
                status_code=API_HTTP_401_UNAUTHORIZED, content=API_MIDDLEWARE_AUTH_UNAUTHORIZED
            )

        if username != settings.metrics_username or password != settings.metrics_password:
            logger.warning(API_MIDDLEWARE_AUTH_LOG_INVALID_BASIC)
            return Response(
                status_code=API_HTTP_403_FORBIDDEN, content=API_MIDDLEWARE_AUTH_FORBIDDEN
            )

        return await call_next(request)
