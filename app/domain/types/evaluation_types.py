# app/domain/types/evaluation_types.py
# DEPRECATED: This module is deprecated and will be removed in a future version.
# Use domain entities from app.domain.entities instead.
#
# Migration guide:
# - Replace EvaluationProtocol with EvaluationEntity from app.domain.entities.evaluation
# - Replace CompetencyScoreProtocol with CompetencyScore from app.domain.entities.evaluation
# - Use EvaluationMapper.orm_to_entity() to convert ORM models to entities

from typing import Protocol, Sequence, Any


class CompetencyScoreProtocol(Protocol):
    """DEPRECATED: Use CompetencyScore from app.domain.entities.evaluation instead.
    
    Minimal fields that domain logic needs from a competency score.

    Use permissive `Any` types to remain compatible with SQLAlchemy Mapped
    attributes used in ORM models (which static type checkers like Pylance
    otherwise consider incompatible with concrete types).
    """
    skill_id: Any
    score: Any


class EvaluationProtocol(Protocol):
    """DEPRECATED: Use EvaluationEntity from app.domain.entities.evaluation instead.
    
    Minimal fields that domain logic needs from an evaluation.

    Conservative typing (using `Any`) avoids Pylance errors when passing
    ORM model instances that use `Mapped[...]` attributes.
    """
    status: Any
    evaluator_relationship: Any
    # Use Any here because ORM models use `Mapped[list[EvaluationCompetencyScore]]`
    # which static checkers consider incompatible with Sequence[...] due to
    # invariance. `Any` silences that while still expressing required access.
    competency_scores: Any
