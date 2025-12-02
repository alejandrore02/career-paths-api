"""Database repositories package."""

# Core repositories
from app.db.repositories.core import (
    UserRepository,
    RoleRepository,
    SkillRepository,
    RoleSkillRequirementRepository,
)

# Evaluation repositories
from app.db.repositories.evaluation import (
    EvaluationCycleRepository,
    EvaluationRepository,
    CompetencyScoreRepository,
    UserSkillScoreRepository,
)

# Skills Assessment repositories
from app.db.repositories.skills_assessment import (
    SkillsAssessmentRepository,
    SkillsAssessmentItemRepository,
)

# Career Path repositories
from app.db.repositories.career_path import (
    CareerPathRepository,
    CareerPathStepRepository,
    DevelopmentActionRepository,
)

# Infrastructure repositories
from app.db.repositories.infrastructure import (
    AICallsLogRepository,
)

__all__ = [
    # Core
    "UserRepository",
    "RoleRepository",
    "SkillRepository",
    "RoleSkillRequirementRepository",
    # Evaluation
    "EvaluationCycleRepository",
    "EvaluationRepository",
    "CompetencyScoreRepository",
    "UserSkillScoreRepository",
    # Skills Assessment
    "SkillsAssessmentRepository",
    "SkillsAssessmentItemRepository",
    # Career Path
    "CareerPathRepository",
    "CareerPathStepRepository",
    "DevelopmentActionRepository",
    # Infrastructure
    "AICallsLogRepository",
]
