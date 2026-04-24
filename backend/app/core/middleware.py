"""
Security and observability middleware.
- Security headers (SEC-09, SEC-10, SEC-24, SEC-25)
- Correlation ID for request tracing
- Global exception handler (SEC-11)
"""

import uuid

import structlog
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

logger = structlog.stdlib.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response (SEC-09, SEC-10, SEC-24, SEC-25)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # SEC-09: Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        # SEC-10: Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"
        # SEC-25: Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # SEC-24: Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        # Additional hardening
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        # SEC-08: HSTS in production (1 year, includeSubDomains)
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production (SEC-08).

    Checks the X-Forwarded-Proto header (set by reverse proxies) to determine
    whether the original request was HTTP. Only active in production.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if settings.environment != "production":
            return await call_next(request)

        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto == "http":
            url = request.url.replace(scheme="https")
            return Response(
                status_code=301,
                headers={"Location": str(url)},
            )

        return await call_next(request)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID to every request for tracing (SEC-11)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = request.headers.get(
            "X-Correlation-ID", str(uuid.uuid4())
        )
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return safe error responses (SEC-11)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Let FastAPI handle HTTP exceptions (401, 403, 404, 429, etc.)
            raise
        except Exception as exc:
            import traceback
            traceback.print_exc()
            correlation_id = structlog.contextvars.get_contextvars().get(
                "correlation_id", "unknown"
            )
            logger.exception("unhandled_exception", path=request.url.path)
            return Response(
                content=(
                    '{"status":"error",'
                    f'"message":"Internal server error",'
                    f'"correlation_id":"{correlation_id}"}}'
                ),
                status_code=500,
                media_type="application/json",
            )
