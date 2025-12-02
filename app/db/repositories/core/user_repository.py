"""
User repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(
        self,
        user_id: UUID,
        load_relationships: bool = False,
    ) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            load_relationships: Whether to eager load role, manager, etc.
        """
        query = select(User).where(User.id == user_id)
        
        if load_relationships:
            query = query.options(
                selectinload(User.role),
                selectinload(User.manager),
                selectinload(User.direct_reports),
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Get all active users with pagination."""
        query = (
            select(User)
            .where(User.is_active == True)
            .order_by(User.full_name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Get all users (active and inactive) with pagination."""
        query = (
            select(User)
            .order_by(User.full_name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_role_id(
        self,
        role_id: UUID,
        active_only: bool = True,
    ) -> list[User]:
        """Get all users with a specific role."""
        query = select(User).where(User.role_id == role_id)
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.order_by(User.full_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_manager_id(
        self,
        manager_id: UUID,
        active_only: bool = True,
    ) -> list[User]:
        """Get all direct reports of a manager."""
        query = select(User).where(User.manager_id == manager_id)
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.order_by(User.full_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete a user (hard delete)."""
        await self.session.delete(user)
        await self.session.flush()

    async def soft_delete(self, user: User) -> User:
        """Soft delete a user by marking as inactive."""
        user.is_active = False
        return await self.update(user)
