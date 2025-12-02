"""
Schemas module.

Schemas are organized by domain:
- core: User, Role, Skill schemas
- evaluation: 360° Evaluation schemas
- skills_assessment: AI Skills Assessment schemas
- career_path: AI Career Path schemas
"""

# Core schemas
from app.schemas.core import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserSummary,
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    SkillBase,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
)

# Evaluation schemas
from app.schemas.evaluation import (
    EvaluationCycleBase,
    EvaluationCycleCreate,
    EvaluationCycleUpdate,
    EvaluationCycleResponse,
    CompetencyScoreBase,
    CompetencyScoreCreate,
    CompetencyScoreResponse,
    EvaluationBase,
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationResponse,
    EvaluationWithScores,
    UserSkillScoreResponse,
    UserSkillProfile,
)

# Skills Assessment schemas
from app.schemas.skills_assessment import (
    SkillsAssessmentItemBase,
    SkillsAssessmentItemResponse,
    SkillsAssessmentBase,
    SkillsAssessmentCreate,
    SkillsAssessmentUpdate,
    SkillsAssessmentResponse,
    SkillsAssessmentWithItems,
    SkillsAssessmentSummary,
)

# Career Path schemas
from app.schemas.career_path import (
    DevelopmentActionBase,
    DevelopmentActionResponse,
    CareerPathStepBase,
    CareerPathStepResponse,
    CareerPathStepWithActions,
    CareerPathBase,
    CareerPathCreate,
    CareerPathUpdate,
    CareerPathResponse,
    CareerPathWithSteps,
    CareerPathSummary,
    AcceptCareerPathRequest,
)

__all__ = [
    # Core
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserSummary",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "SkillBase",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    # Evaluation
    "EvaluationCycleBase",
    "EvaluationCycleCreate",
    "EvaluationCycleUpdate",
    "EvaluationCycleResponse",
    "CompetencyScoreBase",
    "CompetencyScoreCreate",
    "CompetencyScoreResponse",
    "EvaluationBase",
    "EvaluationCreate",
    "EvaluationUpdate",
    "EvaluationResponse",
    "EvaluationWithScores",
    "UserSkillScoreResponse",
    "UserSkillProfile",
    # Skills Assessment
    "SkillsAssessmentItemBase",
    "SkillsAssessmentItemResponse",
    "SkillsAssessmentBase",
    "SkillsAssessmentCreate",
    "SkillsAssessmentUpdate",
    "SkillsAssessmentResponse",
    "SkillsAssessmentWithItems",
    "SkillsAssessmentSummary",
    # Career Path
    "DevelopmentActionBase",
    "DevelopmentActionResponse",
    "CareerPathStepBase",
    "CareerPathStepResponse",
    "CareerPathStepWithActions",
    "CareerPathBase",
    "CareerPathCreate",
    "CareerPathUpdate",
    "CareerPathResponse",
    "CareerPathWithSteps",
    "CareerPathSummary",
    "AcceptCareerPathRequest",
]
