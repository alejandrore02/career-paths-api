"""
Role repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Role


class RoleRepository:
    """Repository for Role model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, role: Role) -> Role:
        """Create a new role."""
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def get_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID."""
        query = select(Role).where(Role.id == role_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        query = select(Role).where(Role.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_active(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Role]:
        """Get all active roles with pagination."""
        query = (
            select(Role)
            .where(Role.is_active == True)
            .order_by(Role.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Role]:
        """Get all roles (active and inactive) with pagination."""
        query = (
            select(Role)
            .order_by(Role.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_job_family(
        self,
        job_family: str,
        active_only: bool = True,
    ) -> list[Role]:
        """Get all roles in a job family."""
        query = select(Role).where(Role.job_family == job_family)
        
        if active_only:
            query = query.where(Role.is_active == True)
        
        query = query.order_by(Role.seniority_level, Role.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, role: Role) -> Role:
        """Update an existing role."""
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def delete(self, role: Role) -> None:
        """Delete a role (hard delete)."""
        await self.session.delete(role)
        await self.session.flush()
