"""Domain entities package.

This package contains pure domain entities (business objects) with rich behavior.
These entities are independent of frameworks, ORMs, and external concerns.

Entities vs Value Objects:
- Entities have identity (ID) and lifecycle
- Value Objects are immutable and identified by their attributes

Usage:
    from app.domain.entities.evaluation import EvaluationEntity, CompetencyScore
    from app.domain.entities.skill_profile import SkillProfile, UserSkillScore
    from app.domain.entities.career_path import CareerPathEntity, CareerPathStep
"""

from app.domain.entities.evaluation import (
    EvaluationEntity,
    CompetencyScore,
)
from app.domain.entities.skill_profile import (
    SkillProfile,
    UserSkillScore,
)
from app.domain.entities.career_path import (
    CareerPathEntity,
    CareerPathStep,
    DevelopmentAction,
)

__all__ = [
    # Evaluation
    "EvaluationEntity",
    "CompetencyScore",
    # Skill Profile
    "SkillProfile",
    "UserSkillScore",
    # Career Path
    "CareerPathEntity",
    "CareerPathStep",
    "DevelopmentAction",
]
