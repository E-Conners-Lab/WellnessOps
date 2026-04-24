"""
Structured logging configuration.
Ensures no PII or secrets in logs (SEC-18).
Uses correlation IDs for request tracing.
"""

import structlog

from app.core.config import settings

# Fields to redact from log output (SEC-18)
REDACTED_FIELDS = frozenset({
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "authorization",
    "cookie",
    "ssn",
    "api_key",
    "jwt_secret",
    "anthropic_api_key",
})

REDACTION_MARKER = "[REDACTED]"


def _redact_sensitive_fields(
    logger: object, method_name: str, event_dict: dict
) -> dict:
    """Redact sensitive fields from log output (SEC-18)."""
    for key in list(event_dict.keys()):
        if key.lower() in REDACTED_FIELDS:
            event_dict[key] = REDACTION_MARKER
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    is_prod = settings.environment == "production"

    renderer = (
        structlog.processors.JSONRenderer()
        if is_prod
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_sensitive_fields,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
