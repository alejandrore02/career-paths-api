"""
Evaluation repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Evaluation,
    EvaluationCycle,
    EvaluationCompetencyScore,
    UserSkillScore,
)

class EvaluationCycleRepository:
    """Repository for EvaluationCycle model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, cycle: EvaluationCycle) -> EvaluationCycle:
        """Create a new evaluation cycle."""
        self.session.add(cycle)
        await self.session.flush()
        await self.session.refresh(cycle)
        return cycle

    async def get_by_id(self, cycle_id: UUID) -> Optional[EvaluationCycle]:
        """Get evaluation cycle by ID."""
        query = select(EvaluationCycle).where(EvaluationCycle.id == cycle_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_cycles(self) -> list[EvaluationCycle]:
        """Get all active evaluation cycles."""
        query = (
            select(EvaluationCycle)
            .where(EvaluationCycle.status == "active")
            .order_by(EvaluationCycle.start_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> list[EvaluationCycle]:
        """Get evaluation cycles by status."""
        query = (
            select(EvaluationCycle)
            .where(EvaluationCycle.status == status)
            .order_by(EvaluationCycle.start_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(self) -> list[EvaluationCycle]:
        """Get all evaluation cycles."""
        query = select(EvaluationCycle).order_by(EvaluationCycle.start_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, cycle: EvaluationCycle) -> EvaluationCycle:
        """Update an existing evaluation cycle."""
        await self.session.flush()
        await self.session.refresh(cycle)
        return cycle

    async def delete(self, cycle_id: UUID) -> None:
        """Delete evaluation cycle by ID."""
        query = delete(EvaluationCycle).where(EvaluationCycle.id == cycle_id)
        await self.session.execute(query)


class EvaluationRepository:
    """Repository for Evaluation model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create(self, evaluation: Evaluation) -> Evaluation:
        """Create a new evaluation."""
        self.session.add(evaluation)
        await self.session.flush()
        await self.session.refresh(evaluation)
        return evaluation

    async def get_by_id(
        self,
        evaluation_id: UUID,
        load_scores: bool = False,
    ) -> Optional[Evaluation]:
        """
        Get evaluation by ID.
        
        Args:
            evaluation_id: Evaluation UUID
            load_scores: Whether to eager load competency scores
        """
        query = select(Evaluation).where(Evaluation.id == evaluation_id)
        
        if load_scores:
            query = query.options(selectinload(Evaluation.competency_scores))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_and_cycle(
        self,
        user_id: UUID,
        cycle_id: UUID,
        status: Optional[str] = None,
    ) -> list[Evaluation]:
        """Get all evaluations for a user in a specific cycle."""
        query = (
            select(Evaluation)
            .where(
                and_(
                    Evaluation.user_id == user_id,
                    Evaluation.evaluation_cycle_id == cycle_id,
                )
            )
            .options(selectinload(Evaluation.competency_scores))
        )
        
        if status:
            query = query.where(Evaluation.status == status)
        
        query = query.order_by(Evaluation.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_evaluator_and_cycle(
        self,
        evaluator_id: UUID,
        cycle_id: UUID,
    ) -> list[Evaluation]:
        """Get all evaluations done by an evaluator in a cycle."""
        query = select(Evaluation).where(
            and_(
                Evaluation.evaluator_id == evaluator_id,
                Evaluation.evaluation_cycle_id == cycle_id,
            )
        ).order_by(Evaluation.created_at)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_cycle(self, cycle_id: UUID) -> list[Evaluation]:
        """Get all evaluations in a specific cycle."""
        query = (
            select(Evaluation)
            .where(Evaluation.evaluation_cycle_id == cycle_id)
            .order_by(Evaluation.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_evaluations(
        self,
        user_id: Optional[UUID] = None,
        evaluator_id: Optional[UUID] = None,
        cycle_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Evaluation]:
        """
        List evaluations with optional filters.
        
        Args:
            user_id: Filter by user being evaluated
            evaluator_id: Filter by evaluator
            cycle_id: Filter by evaluation cycle
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset
        """
        query = select(Evaluation)
        
        conditions = []
        if user_id:
            conditions.append(Evaluation.user_id == user_id)
        if evaluator_id:
            conditions.append(Evaluation.evaluator_id == evaluator_id)
        if cycle_id:
            conditions.append(Evaluation.evaluation_cycle_id == cycle_id)
        if status:
            conditions.append(Evaluation.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Evaluation.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_relationship(
        self,
        user_id: UUID,
        cycle_id: UUID,
        relationship: str,
    ) -> int:
        """Count evaluations of a specific relationship type for a user in a cycle."""
        from sqlalchemy import func
        
        query = select(func.count(Evaluation.id)).where(
            and_(
                Evaluation.user_id == user_id,
                Evaluation.evaluation_cycle_id == cycle_id,
                Evaluation.evaluator_relationship == relationship,
                Evaluation.status == "submitted",
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(self, evaluation: Evaluation) -> Evaluation:
        """Update an existing evaluation."""
        await self.session.flush()
        await self.session.refresh(evaluation)
        return evaluation


class CompetencyScoreRepository:
    """Repository for EvaluationCompetencyScore model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create_bulk(
        self,
        scores: list[EvaluationCompetencyScore],
    ) -> list[EvaluationCompetencyScore]:
        """Create multiple competency scores at once."""
        self.session.add_all(scores)
        await self.session.flush()
        for score in scores:
            await self.session.refresh(score)
        return scores

    async def get_by_evaluation_id(
        self,
        evaluation_id: UUID,
    ) -> list[EvaluationCompetencyScore]:
        """Get all competency scores for an evaluation."""
        query = (
            select(EvaluationCompetencyScore)
            .where(EvaluationCompetencyScore.evaluation_id == evaluation_id)
            .order_by(EvaluationCompetencyScore.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class UserSkillScoreRepository:
    """Repository for UserSkillScore model operations (aggregated profiles)."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    async def create_bulk(
        self,
        scores: list[UserSkillScore],
    ) -> list[UserSkillScore]:
        """Create multiple user skill scores at once."""
        self.session.add_all(scores)
        await self.session.flush()
        for score in scores:
            await self.session.refresh(score)
        return scores

    async def get_by_user_and_cycle(
        self,
        user_id: UUID,
        cycle_id: UUID,
        source: Optional[str] = None,
    ) -> list[UserSkillScore]:
        """
        Get aggregated skill scores for a user in a cycle.
        
        Args:
            user_id: User UUID
            cycle_id: Evaluation cycle UUID
            source: Optional filter by source (360_aggregated, self_only, etc.)
        """
        query = select(UserSkillScore).where(
            and_(
                UserSkillScore.user_id == user_id,
                UserSkillScore.evaluation_cycle_id == cycle_id,
            )
        )
        
        if source:
            query = query.where(UserSkillScore.source == source)
        
        query = query.order_by(UserSkillScore.score.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_by_user_and_cycle(
        self,
        user_id: UUID,
        cycle_id: UUID,
        source: Optional[str] = None,
    ) -> int:
        """
        Delete existing skill scores (for re-aggregation).
        
        Returns:
            Number of rows deleted
        """
        stmt = delete(UserSkillScore).where(
            and_(
                UserSkillScore.user_id == user_id,
                UserSkillScore.evaluation_cycle_id == cycle_id,
            )
        )
        
        if source:
            stmt = stmt.where(UserSkillScore.source == source)
        
        result = await self.session.execute(stmt)
        # In SQLAlchemy 2.x async, rowcount is available after execute for DML
        count = result.rowcount  # type: ignore[attr-defined]
        await self.session.flush()
        return count
