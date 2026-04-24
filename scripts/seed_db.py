"""
Seed script: create initial admin user (the practitioner).
Usage: python -m scripts.seed_db
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path so app imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.security import hash_password
from app.db.database import async_session_factory, engine
from app.db.models.user import User

from sqlalchemy import select


async def seed() -> None:
    """Create the initial admin user if not present."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == "practitioner@wellnessops.local")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin user already exists: {existing.email}")
            return

        admin = User(
            email="practitioner@wellnessops.local",
            password_hash=hash_password("wellness2026!"),
            full_name="the wellness practitioner",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Created admin user: {admin.email} (id: {admin.id})")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
