"""
Async database engine and session factory.
Uses SQLAlchemy 2.0 async API with asyncpg driver.
SSL enforced in production (SEC-08).
"""

import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Build engine kwargs based on database type
_engine_kwargs: dict = {
    "echo": settings.debug,
}

_is_sqlite = settings.database_url.startswith("sqlite")

if not _is_sqlite:
    # Postgres-specific pool settings
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20
    _engine_kwargs["pool_pre_ping"] = True

    if settings.database_ssl:
        _ssl_context = ssl.create_default_context()
        _engine_kwargs["connect_args"] = {"ssl": _ssl_context}

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
