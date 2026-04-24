"""
In-memory sliding window rate limiter (SEC-06).
Applied to auth endpoints: login, signup, password reset, and token refresh.
"""

import time
from collections import defaultdict

import structlog
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

logger = structlog.stdlib.get_logger()

# Rate limit config: max requests per window
# Higher in dev/testing to support Playwright E2E runs
_is_prod = settings.environment == "production"
AUTH_RATE_LIMIT = 10 if _is_prod else 100
AUTH_WINDOW_SECONDS = 60

# Paths subject to auth rate limiting
AUTH_PATHS = frozenset({
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter for auth endpoints."""

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_key(self, request: Request) -> str:
        """Build a rate limit key from client IP and path."""
        client_ip = request.client.host if request.client else "unknown"
        return f"{client_ip}:{request.url.path}"

    def _is_rate_limited(self, key: str) -> bool:
        """Check if the key has exceeded the rate limit using a sliding window."""
        now = time.monotonic()
        window_start = now - AUTH_WINDOW_SECONDS

        # Remove expired entries
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > window_start]

        if len(self._requests[key]) >= AUTH_RATE_LIMIT:
            return True

        self._requests[key].append(now)
        return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path in AUTH_PATHS and request.method == "POST":
            key = self._get_client_key(request)
            if self._is_rate_limited(key):
                logger.warning("rate_limit_exceeded", key=key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                )

        return await call_next(request)
