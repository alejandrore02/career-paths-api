"""Mapper for Evaluation aggregate (ORM ↔ Entity ↔ Schema)."""
from typing import Optional
from uuid import UUID

from app.db.models.evaluation.evaluation import Evaluation as EvaluationORM
from app.db.models.evaluation.evaluation_competency_score import (
    EvaluationCompetencyScore as CompetencyScoreORM
)
from app.domain.entities.evaluation import EvaluationEntity, CompetencyScore
from app.schemas.evaluation.evaluation import (
    EvaluationResponse,
    EvaluationWithScores,
    CompetencyScoreResponse,
)


class EvaluationMapper:
    """Bidirectional mapping between ORM, Entity, and Schema layers."""
    
    @staticmethod
    def orm_to_entity(orm: EvaluationORM) -> EvaluationEntity:
        """Convert ORM model to Domain Entity.
        
        Args:
            orm: SQLAlchemy ORM instance
            
        Returns:
            EvaluationEntity: Rich domain model with business logic
        """
        return EvaluationEntity(
            id=orm.id,
            user_id=orm.user_id,
            evaluation_cycle_id=orm.evaluation_cycle_id,
            evaluator_id=orm.evaluator_id,
            evaluator_relationship=orm.evaluator_relationship,
            status=orm.status,
            competency_scores=[
                CompetencyScore(
                    skill_id=score.skill_id,
                    score=float(score.score),  # Ensure float (may be Decimal)
                    comments=score.comments
                )
                for score in (orm.competency_scores or [])
            ],
            submitted_at=orm.submitted_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
    
    @staticmethod
    def entity_to_response(
        entity: EvaluationEntity,
        include_scores: bool = False
    ) -> EvaluationResponse | EvaluationWithScores:
        """Convert Domain Entity to API Response Schema.
        
        Args:
            entity: Domain entity
            include_scores: Whether to include competency scores
            
        Returns:
            EvaluationResponse or EvaluationWithScores
        """
        base_data = {
            "id": entity.id,
            "user_id": entity.user_id,
            "evaluation_cycle_id": entity.evaluation_cycle_id,
            "evaluator_id": entity.evaluator_id,
            "evaluator_relationship": entity.evaluator_relationship,
            "status": entity.status,
            "submitted_at": entity.submitted_at,
            "created_at": entity.created_at or None,
            "updated_at": entity.updated_at or None,
        }
        
        if include_scores:
            # Note: CompetencyScoreResponse needs id, evaluation_id, created_at, updated_at
            # which are not in the entity. This is a limitation of the current approach.
            # For now, we'll use the ORM-to-response shortcut for full details.
            return EvaluationWithScores(
                **base_data,
                competency_scores=[]  # Would need ORM data for complete info
            )
        
        return EvaluationResponse(**base_data)
    
    @staticmethod
    def orm_to_response(
        orm: EvaluationORM,
        include_scores: bool = False
    ) -> EvaluationResponse | EvaluationWithScores:
        """Direct ORM to API Response (using Pydantic from_attributes).
        
        This is a shortcut that bypasses entity layer when domain logic
        is not needed. Useful for simple CRUD operations.
        
        Args:
            orm: SQLAlchemy ORM instance
            include_scores: Whether to include competency scores
            
        Returns:
            EvaluationResponse or EvaluationWithScores
        """
        if include_scores:
            return EvaluationWithScores.model_validate(orm)
        return EvaluationResponse.model_validate(orm)
    
    @staticmethod
    def orms_to_entities(orms: list[EvaluationORM]) -> list[EvaluationEntity]:
        """Bulk convert ORM list to Entity list.
        
        Args:
            orms: List of ORM instances
            
        Returns:
            List of domain entities
        """
        return [EvaluationMapper.orm_to_entity(orm) for orm in orms]
