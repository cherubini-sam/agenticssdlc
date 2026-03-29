"""Sliding-window rate limiter keyed by API key (or IP as fallback)."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.api.api_utils import (
    API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM,
    API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS,
    API_MIDDLEWARE_RATELIMIT_WINDOW,
    API_RATELIMIT_EXCEEDED_ERROR_CODE,
)

logger = logging.getLogger(__name__)

EXEMPT_PATHS: frozenset[str] = API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS


class ApiMiddlewareRateLimit(BaseHTTPMiddleware):
    """
    In-memory per-client sliding window. RPM=0 disables it entirely,
    which is handy for local dev and load tests.
    """

    def __init__(self, app, rpm: int = API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM) -> None:
        super().__init__(app)
        self._rpm: int = rpm
        self._window: float = API_MIDDLEWARE_RATELIMIT_WINDOW
        self._buckets: dict[str, deque] = defaultdict(deque)

    def _api_middleware_ratelimit_client_id(self, request: Request) -> str:
        """Use the API key when present so per-key limits work; otherwise fall back to IP."""

        key = request.headers.get("X-API-Key", "")
        if key:
            return key
        if request.client:
            return request.client.host
        return "unknown"

    def _api_middleware_ratelimit_check(self, client_id: str) -> tuple[bool, int, int]:
        """Return (allowed, remaining, retry_after_seconds)."""

        now = time.monotonic()
        bucket = self._buckets[client_id]

        # Drop timestamps that have fallen outside the window
        cutoff = now - self._window
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= self._rpm:
            retry_after = max(1, int(self._window - (now - bucket[0])) + 1)
            return False, 0, retry_after

        bucket.append(now)
        return True, self._rpm - len(bucket), 0

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._rpm == 0 or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        client_id = self._api_middleware_ratelimit_client_id(request)
        allowed, remaining, retry_after = self._api_middleware_ratelimit_check(client_id)

        if not allowed:
            # Truncate the key in logs to avoid leaking secrets
            safe_id = (client_id[:8] + "...") if len(client_id) > 8 else client_id
            logger.warning(
                "Rate limit exceeded: client=%s path=%s",
                safe_id,
                request.url.path,
            )
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self._rpm),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
                content={
                    "detail": "Rate limit exceeded",
                    "error_code": API_RATELIMIT_EXCEEDED_ERROR_CODE,
                    "retry_after_seconds": retry_after,
                },
            )

        response = await call_next(request)
        bucket = self._buckets[client_id]
        response.headers["X-RateLimit-Limit"] = str(self._rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if bucket:
            reset_at = int(time.time() + (self._window - (time.monotonic() - bucket[0])))
            response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response
