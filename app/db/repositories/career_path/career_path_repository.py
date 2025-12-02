"""
Career Path repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CareerPath, CareerPathStep, DevelopmentAction


class CareerPathRepository:
    """Repository for CareerPath model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, career_path: CareerPath) -> CareerPath:
        """Create a new career path."""
        self.session.add(career_path)
        await self.session.flush()
        await self.session.refresh(career_path)
        return career_path

    async def get_by_id(
        self,
        path_id: UUID,
        load_steps: bool = False,
    ) -> Optional[CareerPath]:
        """
        Get career path by ID.
        
        Args:
            path_id: Career path UUID
            load_steps: Whether to eager load steps and development actions
        """
        query = select(CareerPath).where(CareerPath.id == path_id)
        
        if load_steps:
            query = query.options(
                selectinload(CareerPath.steps).selectinload(
                    CareerPathStep.development_actions
                )
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[CareerPath]:
        """
        Get all career paths for a user with optional status filter.
        
        Args:
            user_id: User UUID
            status: Optional filter (proposed, accepted, in_progress, completed, discarded)
            limit: Maximum number of results
            offset: Offset for pagination
        """
        query = select(CareerPath).where(CareerPath.user_id == user_id)
        
        if status:
            query = query.where(CareerPath.status == status)
        
        query = (
            query.order_by(CareerPath.recommended.desc(), CareerPath.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recommended_by_user_id(
        self,
        user_id: UUID,
    ) -> list[CareerPath]:
        """Get all recommended career paths for a user."""
        query = (
            select(CareerPath)
            .where(
                and_(
                    CareerPath.user_id == user_id,
                    CareerPath.recommended == True,
                    CareerPath.status.in_(["proposed", "accepted", "in_progress"]),
                )
            )
            .order_by(CareerPath.feasibility_score.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_assessment_id(
        self,
        assessment_id: UUID,
    ) -> list[CareerPath]:
        """Get all career paths generated from a specific skills assessment."""
        query = (
            select(CareerPath)
            .where(CareerPath.skills_assessment_id == assessment_id)
            .order_by(CareerPath.recommended.desc(), CareerPath.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, career_path: CareerPath) -> CareerPath:
        """Update an existing career path."""
        await self.session.flush()
        await self.session.refresh(career_path)
        return career_path

    async def accept_path(self, path_id: UUID, user_id: UUID) -> Optional[CareerPath]:
        """
        Accept a career path and mark others as discarded.
        
        Args:
            path_id: Career path UUID to accept
            user_id: User UUID (for validation)
        """
        # Get the path to accept
        path = await self.get_by_id(path_id)
        if not path or path.user_id != user_id:
            return None
        
        # Mark as accepted
        path.status = "accepted"
        
        # Mark other proposed/accepted paths as alternative
        from sqlalchemy import update
        stmt = (
            update(CareerPath)
            .where(
                and_(
                    CareerPath.user_id == user_id,
                    CareerPath.id != path_id,
                    CareerPath.status.in_(["proposed", "accepted"]),
                )
            )
            .values(status="discarded")
        )
        await self.session.execute(stmt)
        
        await self.session.flush()
        await self.session.refresh(path)
        return path


class CareerPathStepRepository:
    """Repository for CareerPathStep model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create_bulk(
        self,
        steps: list[CareerPathStep],
    ) -> list[CareerPathStep]:
        """Create multiple career path steps at once."""
        self.session.add_all(steps)
        await self.session.flush()
        for step in steps:
            await self.session.refresh(step)
        return steps

    async def get_by_path_id(
        self,
        path_id: UUID,
        load_actions: bool = False,
    ) -> list[CareerPathStep]:
        """
        Get all steps for a career path, ordered by step number.
        
        Args:
            path_id: Career path UUID
            load_actions: Whether to eager load development actions
        """
        query = (
            select(CareerPathStep)
            .where(CareerPathStep.career_path_id == path_id)
            .order_by(CareerPathStep.step_number)
        )
        
        if load_actions:
            query = query.options(selectinload(CareerPathStep.development_actions))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class DevelopmentActionRepository:
    """Repository for DevelopmentAction model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create_bulk(
        self,
        actions: list[DevelopmentAction],
    ) -> list[DevelopmentAction]:
        """Create multiple development actions at once."""
        self.session.add_all(actions)
        await self.session.flush()
        for action in actions:
            await self.session.refresh(action)
        return actions

    async def get_by_step_id(
        self,
        step_id: UUID,
        action_type: Optional[str] = None,
    ) -> list[DevelopmentAction]:
        """
        Get all development actions for a career path step.
        
        Args:
            step_id: Career path step UUID
            action_type: Optional filter (course, project, mentoring, shadowing, certification)
        """
        query = select(DevelopmentAction).where(
            DevelopmentAction.career_path_step_id == step_id
        )
        
        if action_type:
            query = query.where(DevelopmentAction.action_type == action_type)
        
        query = query.order_by(DevelopmentAction.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())
