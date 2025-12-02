"""Evaluation service: create evaluations, aggregate scores and orchestrate AI flows."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.core.logging import get_logger
from app.db.models import Evaluation, EvaluationCompetencyScore, UserSkillScore
from app.db.unit_of_work import UnitOfWork
from app.schemas.evaluation.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationWithScores,
    UserSkillProfile,
)
from app.schemas.mappers.evaluation_mapper import EvaluationMapper
from app.domain.evaluation_logic import (
    is_cycle_complete_for_user,
    aggregate_competency_scores,
)
from app.integrations.ai_skills_client import AISkillsClient

logger = get_logger(__name__)


class EvaluationService:

    def __init__(
        self,
        uow: UnitOfWork,
        ai_skills_client: AISkillsClient,
    ) -> None:
        self.uow = uow
        self.ai_skills_client = ai_skills_client
        

        
    async def create_evaluation(self, data: EvaluationCreate) -> EvaluationResponse:
        """Create a new 360° evaluation and its competency scores.

        Raises NotFoundError/ValidationError on invalid input.
        """
        logger.info(
            f"Creating evaluation for user {data.user_id} "
            f"by evaluator {data.evaluator_id} "
            f"(relationship: {data.evaluator_relationship})"
        )
        
        user = await self.uow.users.get_by_id(data.user_id)

        if not user:
            raise NotFoundError(f"User {data.user_id} not found")
        
        evaluator = await self.uow.users.get_by_id(data.evaluator_id)

        if not evaluator:
            raise NotFoundError(f"Evaluator {data.evaluator_id} not found")
        
        cycle = await self.uow.evaluation_cycles.get_by_id(data.evaluation_cycle_id)

        if not cycle:
            raise NotFoundError(f"Evaluation cycle {data.evaluation_cycle_id} not found")
        
        if cycle.status != "active":
            raise ValidationError(
                f"Cannot create evaluation: cycle is not active (current status: {cycle.status})"
            )
        
        # Create evaluation record with status='submitted'
        evaluation = Evaluation(
            id=uuid4(),
            user_id=data.user_id,
            evaluation_cycle_id=data.evaluation_cycle_id,
            evaluator_id=data.evaluator_id,
            evaluator_relationship=data.evaluator_relationship,
            status="submitted",  # As per flows.md: evaluations are created as submitted
            submitted_at=datetime.now(timezone.utc),
        )
        
        created_evaluation = await self.uow.evaluations.create(evaluation)
        
        # Create competency scores
        competency_names = {c.competency_name for c in data.competencies}
        skills = await self.uow.skills.get_by_names(list(competency_names))
        name_to_skill = {s.name: s for s in skills}

        missing = competency_names - set(name_to_skill.keys())
        if missing:
            raise ValidationError(
                f"Invalid competencies: {sorted(missing)} not found in skills catalog"
            )

        competency_scores = []
        for comp_data in data.competencies:
            skill = name_to_skill[comp_data.competency_name]
            comp_score = EvaluationCompetencyScore(
                id=uuid4(),
                evaluation_id=created_evaluation.id,
                skill_id=skill.id,
                score=comp_data.score,
                comments=comp_data.comments,
            )
            competency_scores.append(comp_score)
        await self.uow.competency_scores.create_bulk(competency_scores)
        await self.uow.commit()
        
        logger.info(
            f"Created evaluation {created_evaluation.id} with "
            f"{len(competency_scores)} competency scores"
        )
        
        # Use mapper to convert ORM model to API response schema
        return EvaluationMapper.orm_to_response(created_evaluation)

    async def get_evaluation(
        self,
        evaluation_id: UUID,
        include_scores: bool = False,
    ) -> EvaluationResponse | EvaluationWithScores:
        """
        Get evaluation by ID.
        """
        evaluation = await self.uow.evaluations.get_by_id(
            evaluation_id,
            load_scores=include_scores,
        )
        
        if not evaluation:
            raise NotFoundError(f"Evaluation {evaluation_id} not found")
        
        # Use mapper to convert ORM model to API response schema
        if include_scores:
            return EvaluationWithScores.model_validate(evaluation)
        
        return EvaluationMapper.orm_to_response(evaluation)

    async def list_evaluations(
        self,
        user_id: Optional[UUID] = None,
        evaluator_id: Optional[UUID] = None,
        cycle_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EvaluationResponse]:
        """
        List evaluations with optional filters.
        
        Args:
            user_id: Filter by user being evaluated
            evaluator_id: Filter by evaluator
            cycle_id: Filter by evaluation cycle
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of evaluations (can be empty)
        """
        evaluations = await self.uow.evaluations.list_evaluations(
            user_id=user_id,
            evaluator_id=evaluator_id,
            cycle_id=cycle_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        return [EvaluationMapper.orm_to_response(e) for e in evaluations]


    async def process_evaluation(self, evaluation_id: UUID) -> dict:
        """Process an evaluation: check completeness, aggregate scores and prepare for AI flows."""
        logger.info(f"Processing evaluation {evaluation_id}")

        # Retrieve the evaluation
        evaluation = await self.uow.evaluations.get_by_id(evaluation_id)
        if not evaluation:
            raise NotFoundError(f"Evaluation {evaluation_id} not found")
        
        user_id = evaluation.user_id
        cycle_id = evaluation.evaluation_cycle_id
        
        logger.info(f"Processing evaluation for user {user_id} in cycle {cycle_id}")

        # Load all evaluations for user in cycle
        user_evaluations_orm = await self.uow.evaluations.get_by_user_and_cycle(
            user_id=user_id,
            cycle_id=cycle_id,
        )
        
        # Convert ORM models to domain entities
        user_evaluations = [EvaluationMapper.orm_to_entity(e) for e in user_evaluations_orm]
        
        # Check if cycle is complete using domain logic
        is_complete, reason = is_cycle_complete_for_user(user_evaluations)
        
        if not is_complete:
            # Cannot proceed with AI processing if cycle is incomplete
            # This ensures we have sufficient 360° feedback for accurate assessment
            raise ConflictError(
                f"Cycle not complete for user. {reason}. "
                f"Cannot proceed with AI processing."
            )
        
        logger.info(f"Cycle complete for user {user_id}. Proceeding with aggregation.")

        # Aggregate scores into user_skill_scores
        await self._aggregate_user_skill_scores(
            user_id=user_id,
            cycle_id=cycle_id,
        )
        await self.uow.commit()
        
        # Note: skills assessment and career-path generation are handled by other services
        
        logger.info(
            f"Evaluation {evaluation_id} processed successfully. "
            f"User {user_id} ready for AI Skills Assessment."
        )
        
        return {
            "evaluation_id": evaluation_id,
            "user_id": user_id,
            "cycle_id": cycle_id,
            "cycle_complete": True,
            "message": "Evaluation processed. Ready for Skills Assessment.",
        }

    async def _aggregate_user_skill_scores(self, user_id: UUID, cycle_id: UUID) -> None:
        """Aggregate evaluation scores into `user_skill_scores` (delete then insert)."""
        logger.info(
            f"Aggregating skill scores for user {user_id} in cycle {cycle_id}"
        )
        
        # Use domain logic to aggregate competency scores
        stmt = (
            select(Evaluation)
            .where(
                Evaluation.user_id == user_id,
                Evaluation.evaluation_cycle_id == cycle_id,
                Evaluation.status == "submitted",
            )
            .options(
                selectinload(Evaluation.competency_scores)
            )
        )
        # Use the UnitOfWork's session to execute the query
        session = self.uow.session

        result = await session.execute(stmt)
        evaluations_orm = result.scalars().unique().all()
        
        # Convert ORM models to domain entities
        evaluations = [EvaluationMapper.orm_to_entity(e) for e in evaluations_orm]

        aggregated = aggregate_competency_scores(evaluations)
        
        # Step 3.2: Delete old user_skill_scores for this user/cycle
        # This ensures we don't have stale data from previous aggregations
        # Important: This is done in the same transaction as the insert below
        # so we never have an inconsistent state
        deleted_count = await self.uow.user_skill_scores.delete_by_user_and_cycle(
            user_id=user_id,
            cycle_id=cycle_id,
        )
        
        logger.info(
            f"Deleted {deleted_count} old skill scores for user {user_id}"
        )
        
        # Step 3.3: Create new user_skill_scores
        # Each skill gets one consolidated record with:
        # - score: overall average across all evaluator relationships (0.0-10.0)
        # - confidence: measure of how reliable the score is (0.0-1.0)
        # - raw_stats: JSONB with detailed breakdown by relationship
        new_scores = []
        
        for skill_id, stats in aggregated.items():
            user_skill_score = UserSkillScore(
                id=uuid4(),
                user_id=user_id,
                evaluation_cycle_id=cycle_id,
                skill_id=skill_id,
                source="360_aggregated",  # Indicates this comes from 360° evaluations
                score=stats["overall_avg"],  # Weighted average across all relationships
                confidence=stats["confidence"],  # Range: 0.0-1.0, higher with more evaluations
                raw_stats=stats["raw_stats"],  # JSONB: {self_avg, peer_avg, manager_avg, etc.}
            )
            new_scores.append(user_skill_score)
        
        # Step 3.4: Bulk insert new scores
        # Bulk operation is more efficient than individual inserts
        if new_scores:
            await self.uow.user_skill_scores.create_bulk(new_scores)
            logger.info(
                f"Created {len(new_scores)} aggregated skill scores for user {user_id}"
            )
        
        # Transaction will be committed by caller
        # This ensures atomicity: delete + insert happen together or not at all

    async def get_user_skill_profile(
        self,
        user_id: UUID,
        cycle_id: UUID,
    ) -> UserSkillProfile:
        """
        Get aggregated skill profile for a user in a cycle.
        """
        scores = await self.uow.user_skill_scores.get_by_user_and_cycle(
            user_id=user_id,
            cycle_id=cycle_id,
        )
        
        if not scores:
            raise NotFoundError(
                f"No skill profile found for user {user_id} in cycle {cycle_id}"
            )
        
        # Convert ORM models to Pydantic response schemas
        from app.schemas.evaluation.evaluation import UserSkillScoreResponse
        
        return UserSkillProfile(
            user_id=user_id,
            evaluation_cycle_id=cycle_id,
            skill_scores=[UserSkillScoreResponse.model_validate(s) for s in scores],
        )
