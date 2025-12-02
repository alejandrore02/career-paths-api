"""
Database models module.

Models are organized by domain:
- core: Identity and organization (User, Role, Skill, RoleSkillRequirement)
- evaluation: 360° Evaluations (EvaluationCycle, Evaluation, EvaluationCompetencyScore, UserSkillScore)
- skills_assessment: AI Skills Assessment (SkillsAssessment, SkillsAssessmentItem)
- career_path: AI Career Paths (CareerPath, CareerPathStep, DevelopmentAction)
- infrastructure: Audit and infrastructure (AICallsLog)
"""

# Core models
from app.db.models.core import (
    User,
    Role,
    Skill,
    RoleSkillRequirement,
)

# Evaluation models
from app.db.models.evaluation import (
    EvaluationCycle,
    Evaluation,
    EvaluationCompetencyScore,
    UserSkillScore,
)

# Skills Assessment models
from app.db.models.skills_assessment import (
    SkillsAssessment,
    SkillsAssessmentItem,
)

# Career Path models
from app.db.models.career_path import (
    CareerPath,
    CareerPathStep,
    DevelopmentAction,
)

# Infrastructure models
from app.db.models.infrastructure import (
    AICallsLog,
)

__all__ = [
    # Core
    "User",
    "Role",
    "Skill",
    "RoleSkillRequirement",
    # Evaluation
    "EvaluationCycle",
    "Evaluation",
    "EvaluationCompetencyScore",
    "UserSkillScore",
    # Skills Assessment
    "SkillsAssessment",
    "SkillsAssessmentItem",
    # Career Path
    "CareerPath",
    "CareerPathStep",
    "DevelopmentAction",
    # Infrastructure
    "AICallsLog",
]

