"""
Application configuration via environment variables.
Secrets loaded from env or Vault -- never hardcoded (SEC-12).
Production startup validates that all required secrets are configured.
"""

import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "WellnessOps"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database (SEC-13: separate creds per environment)
    database_url: str = "postgresql+asyncpg://wellnessops:localdev@localhost:5432/wellnessops"
    database_ssl: bool = False  # Set true in production for SSL-only connections

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8100

    # LLM Backend: "claude" or "ollama"
    llm_backend: str = "ollama"

    # Claude API (SEC-12: loaded from env, never in code)
    anthropic_api_key: str = ""
    claude_opus_model: str = "claude-opus-4-20250514"
    claude_sonnet_model: str = "claude-sonnet-4-20250514"

    # Ollama (local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_fast_model: str = "llama3.1:8b"
    ollama_reasoning_model: str = "llama3.1:8b"
    ollama_vision_model: str = "gemma3:12b"

    # PII Encryption (AES-256-GCM)
    pii_encryption_key: str = ""

    # Auth (SEC-16, SEC-17)
    jwt_secret: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # File uploads (SEC-22)
    upload_dir: str = "/data/uploads"
    max_upload_size_mb: int = 25
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp", "image/heic"]
    allowed_document_types: list[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # RAG
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    chunk_size: int = 512
    chunk_overlap: int = 50
    rag_top_k: int = 10

    # PDF Reports
    report_template_dir: str = "app/templates/reports"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def validate_production_secrets(self) -> list[str]:
        """Check that all required secrets are properly configured for production.

        Returns a list of error messages. Empty list means all checks pass.
        """
        errors: list[str] = []

        if self.jwt_secret == "CHANGE-ME-IN-PRODUCTION":
            errors.append("JWT_SECRET is still the default value. Set a strong random secret.")

        if not self.pii_encryption_key:
            errors.append(
                "PII_ENCRYPTION_KEY is not set. Generate with: "
                "python -c \"import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())\""
            )

        if self.llm_backend == "claude" and not self.anthropic_api_key:
            errors.append("LLM_BACKEND is 'claude' but ANTHROPIC_API_KEY is not set.")

        # Only require SSL if database is on an external host (not Docker internal)
        is_internal_db = any(
            host in self.database_url
            for host in ("localhost", "127.0.0.1", "db:", "host.docker.internal")
        )
        if not self.database_ssl and not is_internal_db:
            errors.append("DATABASE_SSL should be true for external database connections.")

        if self.debug:
            errors.append("DEBUG is true in production. Set DEBUG=false.")

        return errors


settings = Settings()

# Fail fast in production if secrets are misconfigured
if settings.environment == "production":
    _errors = settings.validate_production_secrets()
    if _errors:
        print("FATAL: Production security validation failed:", file=sys.stderr)
        for err in _errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
