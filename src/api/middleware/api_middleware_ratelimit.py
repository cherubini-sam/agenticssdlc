"""Sliding-window rate limiter keyed by API key (or IP as fallback)."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.api.api_utils import (
    API_HEADER_API_KEY,
    API_HTTP_429_TOO_MANY_REQUESTS,
    API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM,
    API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS,
    API_MIDDLEWARE_RATELIMIT_WINDOW,
    API_RATELIMIT_CLIENT_UNKNOWN,
    API_RATELIMIT_DETAIL_EXCEEDED,
    API_RATELIMIT_EXCEEDED_ERROR_CODE,
    API_RATELIMIT_HEADER_LIMIT,
    API_RATELIMIT_HEADER_REMAINING,
    API_RATELIMIT_HEADER_RESET,
    API_RATELIMIT_HEADER_RETRY_AFTER,
    API_RATELIMIT_LOG_EXCEEDED,
)

logger = logging.getLogger(__name__)

EXEMPT_PATHS: frozenset[str] = API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS


class ApiMiddlewareRateLimit(BaseHTTPMiddleware):
    """
    In-memory per-client sliding window. RPM=0 disables it entirely,
    which is handy for local dev and load tests.
    """

    def __init__(self, app, rpm: int = API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM) -> None:
        """
        Args:
            app: ASGI application.
            rpm: Maximum requests per minute per client. 0 disables rate
                limiting entirely.
        """
        super().__init__(app)
        self._rpm: int = rpm
        self._window: float = API_MIDDLEWARE_RATELIMIT_WINDOW
        self._buckets: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _api_middleware_ratelimit_client_id(self, request: Request) -> str:
        """Use the API key when present so per-key limits work; otherwise fall back to IP.

        Args:
            request: Starlette request.

        Returns:
            API key string when present in headers, client host IP as fallback,
            or "unknown" if neither is available.
        """

        key = request.headers.get(API_HEADER_API_KEY, "")
        if key:
            return key
        if request.client:
            return request.client.host
        return API_RATELIMIT_CLIENT_UNKNOWN

    def _api_middleware_ratelimit_check(self, client_id: str) -> tuple[bool, int, int]:
        """Evaluate whether the client is within its rate-limit budget.

        Args:
            client_id: Identifier string for the requesting client.

        Returns:
            Tuple of (allowed, remaining, retry_after_seconds); allowed is False
            when the bucket is full.
        """

        now = time.monotonic()

        with self._lock:
            bucket = self._buckets[client_id]

            # Drop timestamps that have fallen outside the window
            cutoff = now - self._window
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self._rpm:
                retry_after = max(1, int(self._window - (now - bucket[0])) + 1)
                return False, 0, retry_after

            bucket.append(now)
            # Evict empty buckets to prevent unbounded dict growth under many unique clients
            self._buckets = defaultdict(deque, {k: v for k, v in self._buckets.items() if v})
            return True, self._rpm - len(bucket), 0

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._rpm == 0 or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        client_id = self._api_middleware_ratelimit_client_id(request)
        allowed, remaining, retry_after = self._api_middleware_ratelimit_check(client_id)

        if not allowed:
            # Truncate the key in logs to avoid leaking secrets
            safe_id = (client_id[:8] + "...") if len(client_id) > 8 else client_id
            logger.warning(API_RATELIMIT_LOG_EXCEEDED, safe_id, request.url.path)
            return JSONResponse(
                status_code=API_HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    API_RATELIMIT_HEADER_RETRY_AFTER: str(retry_after),
                    API_RATELIMIT_HEADER_LIMIT: str(self._rpm),
                    API_RATELIMIT_HEADER_REMAINING: "0",
                    API_RATELIMIT_HEADER_RESET: str(int(time.time()) + retry_after),
                },
                content={
                    "detail": API_RATELIMIT_DETAIL_EXCEEDED,
                    "error_code": API_RATELIMIT_EXCEEDED_ERROR_CODE,
                    "retry_after_seconds": retry_after,
                },
            )

        response = await call_next(request)
        bucket = self._buckets[client_id]
        response.headers[API_RATELIMIT_HEADER_LIMIT] = str(self._rpm)
        response.headers[API_RATELIMIT_HEADER_REMAINING] = str(remaining)
        if bucket:
            reset_at = int(time.time() + (self._window - (time.monotonic() - bucket[0])))
            response.headers[API_RATELIMIT_HEADER_RESET] = str(reset_at)
        return response
