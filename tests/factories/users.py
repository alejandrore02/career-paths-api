# tests/factories/users.py
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def create_user(
    db_session: AsyncSession,
    *,
    email: str = "test.user@example.com",
    full_name: str = "Test User",
    is_active: bool = True,
) -> User:
    """Create a generic active user."""
    user = User(
        id=uuid4(),
        email=email,
        full_name=full_name,
        is_active=is_active,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


async def create_evaluator(
    db_session: AsyncSession,
    *,
    email: str = "evaluator@example.com",
    full_name: str = "Test Evaluator",
) -> User:
    """Create an evaluator user."""
    return await create_user(
        db_session,
        email=email,
        full_name=full_name,
        is_active=True,
    )


async def create_manager(
    db_session: AsyncSession,
    *,
    email: str = "manager@example.com",
    full_name: str = "Test Manager",
) -> User:
    """Create a manager user."""
    return await create_user(
        db_session,
        email=email,
        full_name=full_name,
        is_active=True,
    )
