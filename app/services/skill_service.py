"""
Skill service for business logic orchestration.
"""
from typing import Optional
from uuid import UUID

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.core.logging import get_logger
from app.db.models.core import Skill
from app.db.unit_of_work import UnitOfWork
from app.schemas.core.skill import SkillCreate, SkillUpdate, SkillResponse

logger = get_logger(__name__)


class SkillService:
    """Service for skill operations."""

    def __init__(self, uow: UnitOfWork):
        """Initialize service with Unit of Work."""
        self.uow = uow

    async def create_skill(self, data: SkillCreate) -> SkillResponse:
        """
        Create a new skill.

        Args:
            data: Skill creation data

        Returns:
            Created skill

        Raises:
            ConflictError: If skill name already exists
        """
        # Check name uniqueness
        existing_skill = await self.uow.skills.get_by_name(data.name)
        if existing_skill:
            raise ConflictError(
                message="Skill with this name already exists",
                details={"name": data.name},
            )

        # Create skill
        skill = Skill(
            name=data.name,
            category=data.category,
            description=data.description,
            behavioral_indicators=data.behavioral_indicators,
            is_global=data.is_global,
            is_active=data.is_active,
        )

        created_skill = await self.uow.skills.create(skill)
        await self.uow.session.commit()

        logger.info(
            f"Created skill: {created_skill.name}",
            extra={
                "skill_id": str(created_skill.id),
                "category": created_skill.category,
            },
        )

        return SkillResponse.model_validate(created_skill)

    async def get_skill(self, skill_id: UUID) -> SkillResponse:
        """
        Get skill by ID.

        Args:
            skill_id: Skill UUID

        Returns:
            Skill details

        Raises:
            NotFoundError: If skill not found
        """
        skill = await self.uow.skills.get_by_id(skill_id)
        if not skill:
            raise NotFoundError(
                message="Skill not found",
                details={"skill_id": str(skill_id)},
            )

        return SkillResponse.model_validate(skill)

    async def list_skills(
        self,
        active_only: bool = True,
        category: Optional[str] = None,
        global_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SkillResponse]:
        """
        List skills with optional filters.

        Args:
            active_only: Only return active skills
            category: Filter by category
            global_only: Only return global skills
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of skills
        """
        # Apply specific filters
        if category:
            skills = await self.uow.skills.get_by_category(category, active_only=active_only)
        elif global_only:
            skills = await self.uow.skills.get_global_skills(active_only=active_only)
        elif active_only:
            skills = await self.uow.skills.get_all_active(limit=limit, offset=offset)
        else:
            skills = await self.uow.skills.get_all(limit=limit, offset=offset)

        return [SkillResponse.model_validate(s) for s in skills]

    async def update_skill(self, skill_id: UUID, data: SkillUpdate) -> SkillResponse:
        """
        Update skill.

        Args:
            skill_id: Skill UUID
            data: Update data (partial)

        Returns:
            Updated skill

        Raises:
            NotFoundError: If skill not found
            ConflictError: If name already exists
        """
        # Get existing skill
        skill = await self.uow.skills.get_by_id(skill_id)
        if not skill:
            raise NotFoundError(
                message="Skill not found",
                details={"skill_id": str(skill_id)},
            )

        # Update fields
        update_dict = data.model_dump(exclude_unset=True)

        # Validate name uniqueness
        if "name" in update_dict and update_dict["name"] != skill.name:
            existing_skill = await self.uow.skills.get_by_name(update_dict["name"])
            if existing_skill:
                raise ConflictError(
                    message="Skill with this name already exists",
                    details={"name": update_dict["name"]},
                )

        # Apply updates
        for key, value in update_dict.items():
            setattr(skill, key, value)

        updated_skill = await self.uow.skills.update(skill)
        await self.uow.session.commit()

        logger.info(
            f"Updated skill: {updated_skill.name}",
            extra={"skill_id": str(skill_id), "updated_fields": list(update_dict.keys())},
        )

        return SkillResponse.model_validate(updated_skill)

    async def deactivate_skill(self, skill_id: UUID) -> SkillResponse:
        """
        Deactivate skill (soft delete).

        Args:
            skill_id: Skill UUID

        Returns:
            Deactivated skill

        Raises:
            NotFoundError: If skill not found
        """
        skill = await self.uow.skills.get_by_id(skill_id)
        if not skill:
            raise NotFoundError(
                message="Skill not found",
                details={"skill_id": str(skill_id)},
            )

        skill.is_active = False
        updated_skill = await self.uow.skills.update(skill)
        await self.uow.session.commit()

        logger.info(
            f"Deactivated skill: {updated_skill.name}",
            extra={"skill_id": str(skill_id)},
        )

        return SkillResponse.model_validate(updated_skill)
