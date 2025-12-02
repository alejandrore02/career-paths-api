"""Skill repository for database operations.

Provides CRUD and lookup helpers for the `Skill` model. All methods are
async and operate within the provided `AsyncSession` transaction context.
"""
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Skill


class SkillRepository:
    """Repository for Skill model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, skill: Skill) -> Skill:
        """Create a new skill."""
        self.session.add(skill)
        await self.session.flush()
        await self.session.refresh(skill)
        return skill

    async def get_by_id(self, skill_id: UUID) -> Optional[Skill]:
        """Get skill by ID."""
        query = select(Skill).where(Skill.id == skill_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Skill]:
        """Get skill by exact name."""
        query = select(Skill).where(Skill.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_names(
        self,
        names: Sequence[str],
        *,
        active_only: bool = True,
    ) -> list[Skill]:
        """Get all skills whose name is in the provided collection."""
        if not names:
            return []
        unique_names = list({n for n in names})

        query = select(Skill).where(Skill.name.in_(unique_names))  # type: ignore[arg-type]
        if active_only:
            query = query.where(Skill.is_active == True) 
        query = query.order_by(Skill.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_ids(
        self,
        ids: Sequence[UUID],
        *,
        active_only: bool = True,
    ) -> list[Skill]:
       
        if not ids:
            return []
        unique_ids = list({i for i in ids})

        query = select(Skill).where(Skill.id.in_(unique_ids))  
        if active_only:
            query = query.where(Skill.is_active == True) 
        query = query.order_by(Skill.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())



    async def get_all_active(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Skill]:
        """Get all active skills with pagination."""
        query = (
            select(Skill)
            .where(Skill.is_active == True)
            .order_by(Skill.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Skill]:
        """Get all skills (active and inactive) with pagination."""
        query = (
            select(Skill)
            .order_by(Skill.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())



    async def get_by_category(
        self,
        category: str,
        active_only: bool = True,
    ) -> list[Skill]:
        """Get all skills in a specific category."""
        query = select(Skill).where(Skill.category == category)
        
        if active_only:
            query = query.where(Skill.is_active == True)
        
        query = query.order_by(Skill.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())



    async def get_global_skills(self, active_only: bool = True) -> list[Skill]:
        """Get all global skills."""
        query = select(Skill).where(Skill.is_global == True)
        
        if active_only:
            query = query.where(Skill.is_active == True)
        
        query = query.order_by(Skill.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())



    async def update(self, skill: Skill) -> Skill:
        """Update an existing skill."""
        await self.session.flush()
        await self.session.refresh(skill)
        return skill



    async def delete(self, skill: Skill) -> None:
        """Delete a skill (hard delete)."""
        await self.session.delete(skill)
        await self.session.flush()
