"""
Test fixtures for the WellnessOps backend.
Uses an in-process SQLite database for fast isolated testing.
ChromaDB tests use an ephemeral in-memory client.
"""

import asyncio
import os

# IMPORTANT: Set env vars BEFORE any app imports so Settings() picks them up
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"
os.environ["JWT_SECRET"] = "test-secret-key-do-not-use-in-production"
os.environ["CHROMA_HOST"] = "localhost"
os.environ["CHROMA_PORT"] = "8100"
os.environ["PII_ENCRYPTION_KEY"] = "Xflo5X8fyKteHOxq5i6hwWYqGLdWNbJsg0UchY8Nsbc="
os.environ["LLM_BACKEND"] = "ollama"

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.models.base import Base
from app.db.models.user import User

test_engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user and return it."""
    user = User(
        id=uuid.uuid4(),
        email="test@wellnessops.local",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(test_user: User) -> str:
    """Create a valid access token for the test user."""
    return create_access_token(test_user.id, test_user.role)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, auth_token: str) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated async test client."""
    from app.db.database import get_db
    from app.main import app

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"access_token": auth_token},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauthed_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an unauthenticated async test client."""
    from app.db.database import get_db
    from app.main import app

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
