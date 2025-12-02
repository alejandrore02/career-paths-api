"""
Skills Assessment repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import SkillsAssessment, SkillsAssessmentItem


class SkillsAssessmentRepository:
    """Repository for SkillsAssessment model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, assessment: SkillsAssessment) -> SkillsAssessment:
        """Create a new skills assessment."""
        self.session.add(assessment)
        await self.session.flush()
        await self.session.refresh(assessment)
        return assessment

    async def get_by_id(
        self,
        assessment_id: UUID,
        load_items: bool = False,
    ) -> Optional[SkillsAssessment]:
        """
        Get skills assessment by ID.
        
        Args:
            assessment_id: Assessment UUID
            load_items: Whether to eager load assessment items
        """
        query = select(SkillsAssessment).where(SkillsAssessment.id == assessment_id)
        
        if load_items:
            query = query.options(selectinload(SkillsAssessment.items))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_by_user_id(
        self,
        user_id: UUID,
        load_items: bool = False,
    ) -> Optional[SkillsAssessment]:
        """
        Get latest completed skills assessment for a user.
        
        Args:
            user_id: User UUID
            load_items: Whether to eager load assessment items
        """
        query = (
            select(SkillsAssessment)
            .where(
                and_(
                    SkillsAssessment.user_id == user_id,
                    SkillsAssessment.status == "completed",
                )
            )
            .order_by(SkillsAssessment.processed_at.desc())
            .limit(1)
        )
        
        if load_items:
            query = query.options(selectinload(SkillsAssessment.items))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[SkillsAssessment]:
        """Get all skills assessments for a user with pagination."""
        query = (
            select(SkillsAssessment)
            .where(SkillsAssessment.user_id == user_id)
            .order_by(SkillsAssessment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_user_and_cycle(
        self,
        user_id: UUID,
        cycle_id: UUID,
    ) -> Optional[SkillsAssessment]:
        """Get skills assessment for a user in a specific cycle."""
        query = select(SkillsAssessment).where(
            and_(
                SkillsAssessment.user_id == user_id,
                SkillsAssessment.evaluation_cycle_id == cycle_id,
            )
        ).order_by(SkillsAssessment.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, assessment: SkillsAssessment) -> SkillsAssessment:
        """Update an existing skills assessment."""
        await self.session.flush()
        await self.session.refresh(assessment)
        return assessment


class SkillsAssessmentItemRepository:
    """Repository for SkillsAssessmentItem model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create_bulk(
        self,
        items: list[SkillsAssessmentItem],
    ) -> list[SkillsAssessmentItem]:
        """Create multiple assessment items at once."""
        self.session.add_all(items)
        await self.session.flush()
        for item in items:
            await self.session.refresh(item)
        return items

    async def get_by_assessment_id(
        self,
        assessment_id: UUID,
        item_type: Optional[str] = None,
    ) -> list[SkillsAssessmentItem]:
        """
        Get all items for an assessment, optionally filtered by type.
        
        Args:
            assessment_id: Assessment UUID
            item_type: Optional filter (strength, growth_area, hidden_talent, role_readiness)
        """
        query = select(SkillsAssessmentItem).where(
            SkillsAssessmentItem.skills_assessment_id == assessment_id
        )
        
        if item_type:
            query = query.where(SkillsAssessmentItem.item_type == item_type)
        
        query = query.order_by(SkillsAssessmentItem.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_strengths(self, assessment_id: UUID) -> list[SkillsAssessmentItem]:
        """Get all strength items for an assessment."""
        return await self.get_by_assessment_id(assessment_id, "strength")

    async def get_growth_areas(self, assessment_id: UUID) -> list[SkillsAssessmentItem]:
        """Get all growth area items for an assessment."""
        return await self.get_by_assessment_id(assessment_id, "growth_area")

    async def get_role_readiness(self, assessment_id: UUID) -> list[SkillsAssessmentItem]:
        """Get all role readiness items for an assessment."""
        return await self.get_by_assessment_id(assessment_id, "role_readiness")
