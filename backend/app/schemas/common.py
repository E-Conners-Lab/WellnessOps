"""
Shared response schemas.
Standard API envelope: {status, data, meta} for success, {status, message, correlation_id} for errors (SEC-11).
"""

from typing import Any

from pydantic import BaseModel


class PaginatedMeta(BaseModel):
    """Pagination metadata."""

    page: int = 1
    per_page: int = 20
    total: int = 0


class APIResponse(BaseModel):
    """Standard success response envelope."""

    status: str = "success"
    data: Any = None
    meta: PaginatedMeta | None = None


class ErrorResponse(BaseModel):
    """Standard error response (SEC-11: no stack traces)."""

    status: str = "error"
    message: str
    correlation_id: str | None = None
