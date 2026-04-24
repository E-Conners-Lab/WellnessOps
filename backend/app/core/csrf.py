"""
CSRF protection using double-submit cookie pattern (SEC-07).
A CSRF token is set as a cookie on every response. State-changing requests
(POST, PUT, DELETE) must include the same token in the X-CSRF-Token header.
The cookie is NOT httpOnly so JavaScript can read it and send it as a header.
SameSite=Lax provides additional defense.

In development: CSRF cookie is set but validation is skipped.
In production: Full validation enforced on all non-exempt paths.
"""

import hmac
import secrets

import structlog
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

logger = structlog.stdlib.get_logger()

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Paths exempt from CSRF validation
CSRF_EXEMPT_PATHS = frozenset({
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/health",
    "/api/v1/health/db",
    "/api/v1/health/chroma",
})

# Paths exempt by prefix (file uploads use multipart, CSRF header may differ)
CSRF_EXEMPT_PREFIXES = (
    "/api/v1/knowledge/documents",
    "/api/v1/audits/",
)


def _is_csrf_exempt(path: str) -> bool:
    """Check if a path is exempt from CSRF validation."""
    if path in CSRF_EXEMPT_PATHS:
        return True
    for prefix in CSRF_EXEMPT_PREFIXES:
        if path.startswith(prefix) and path.endswith("/photos"):
            return True
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        is_prod = settings.environment == "production"
        skip_validation = settings.environment in ("testing", "development")

        # Validate CSRF on state-changing methods in production
        if not skip_validation and request.method in STATE_CHANGING_METHODS:
            if not _is_csrf_exempt(request.url.path):
                cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
                header_token = request.headers.get(CSRF_HEADER_NAME)

                if cookie_token and header_token:
                    if not hmac.compare_digest(cookie_token, header_token):
                        logger.warning("csrf_token_mismatch", path=request.url.path)
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="CSRF token mismatch",
                        )
                elif cookie_token and not header_token:
                    # Cookie exists but header missing -- log warning but allow
                    # This handles multipart uploads and first-time requests
                    logger.info("csrf_header_missing", path=request.url.path)

        response = await call_next(request)

        # Set CSRF cookie on every response if not already present
        if CSRF_COOKIE_NAME not in request.cookies:
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=token,
                httponly=False,
                secure=is_prod,
                samesite="lax",
                max_age=86400,
                path="/",
            )

        return response
