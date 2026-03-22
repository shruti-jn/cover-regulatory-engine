"""Seed or update a local admin user for development."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.session import AsyncSessionLocal
from src.models.user import User, UserRole


async def seed_admin(email: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email).limit(1))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(email=email, role=UserRole.ADMIN)
            session.add(user)
            action = "created"
        else:
            user.role = UserRole.ADMIN
            action = "updated"

        await session.commit()
        print(f"{action} admin user: {email}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/seed_local_admin.py <admin-email>")
        return 1

    asyncio.run(seed_admin(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
