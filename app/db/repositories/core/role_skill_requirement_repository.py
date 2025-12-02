"""
Role Skill Requirement repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import RoleSkillRequirement


class RoleSkillRequirementRepository:
    """Repository for RoleSkillRequirement model operations (competency matrix)."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        requirement: RoleSkillRequirement,
    ) -> RoleSkillRequirement:
        """Create a new role skill requirement."""
        self.session.add(requirement)
        await self.session.flush()
        await self.session.refresh(requirement)
        return requirement

    async def create_bulk(
        self,
        requirements: list[RoleSkillRequirement],
    ) -> list[RoleSkillRequirement]:
        """Create multiple role skill requirements at once."""
        self.session.add_all(requirements)
        await self.session.flush()
        for req in requirements:
            await self.session.refresh(req)
        return requirements

    async def get_by_id(
        self,
        requirement_id: UUID,
    ) -> Optional[RoleSkillRequirement]:
        """Get role skill requirement by ID."""
        query = select(RoleSkillRequirement).where(
            RoleSkillRequirement.id == requirement_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_role_id(
        self,
        role_id: UUID,
        is_required: Optional[bool] = None,
    ) -> list[RoleSkillRequirement]:
        """
        Get all skill requirements for a role.
        
        Args:
            role_id: Role UUID
            is_required: Optional filter for required vs optional skills (uses is_core)
        """
        query = select(RoleSkillRequirement).where(
            RoleSkillRequirement.role_id == role_id
        )
        
        if is_required is not None:
            query = query.where(RoleSkillRequirement.is_core == is_required)
        
        query = query.order_by(
            RoleSkillRequirement.is_core.desc(),
            RoleSkillRequirement.required_level.desc(),
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_skill_id(
        self,
        skill_id: UUID,
    ) -> list[RoleSkillRequirement]:
        """Get all roles that require a specific skill."""
        query = (
            select(RoleSkillRequirement)
            .where(RoleSkillRequirement.skill_id == skill_id)
            .order_by(RoleSkillRequirement.required_level.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_role_and_skill(
        self,
        role_id: UUID,
        skill_id: UUID,
    ) -> Optional[RoleSkillRequirement]:
        """Get a specific role skill requirement by role and skill."""
        query = select(RoleSkillRequirement).where(
            and_(
                RoleSkillRequirement.role_id == role_id,
                RoleSkillRequirement.skill_id == skill_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_required_for_role(
        self,
        role_id: UUID,
    ) -> list[RoleSkillRequirement]:
        """Get only required (not optional) skills for a role."""
        return await self.get_by_role_id(role_id, is_required=True)

    async def update(
        self,
        requirement: RoleSkillRequirement,
    ) -> RoleSkillRequirement:
        """Update an existing role skill requirement."""
        await self.session.flush()
        await self.session.refresh(requirement)
        return requirement

    async def delete_by_id(self, requirement_id: UUID) -> bool:
        """
        Delete a role skill requirement by ID.
        
        Returns:
            True if deleted, False if not found
        """
        stmt = delete(RoleSkillRequirement).where(
            RoleSkillRequirement.id == requirement_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0  # type: ignore[attr-defined]

    async def delete_by_role_id(self, role_id: UUID) -> int:
        """
        Delete all skill requirements for a role.
        
        Returns:
            Number of requirements deleted
        """
        stmt = delete(RoleSkillRequirement).where(
            RoleSkillRequirement.role_id == role_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[attr-defined]

    async def replace_role_requirements(
        self,
        role_id: UUID,
        new_requirements: list[RoleSkillRequirement],
    ) -> list[RoleSkillRequirement]:
        """
        Replace all requirements for a role with new ones (atomic operation).
        
        Args:
            role_id: Role UUID
            new_requirements: New list of requirements
            
        Returns:
            Created requirements
        """
        # Delete existing requirements
        await self.delete_by_role_id(role_id)
        
        # Create new requirements
        return await self.create_bulk(new_requirements)
