"""Skills Assessment schemas module."""

from app.schemas.skills_assessment.skills_assessment import (
    # Items
    SkillsAssessmentItemBase,
    SkillsAssessmentItemResponse,
    # Assessment
    SkillsAssessmentBase,
    SkillsAssessmentCreate,
    SkillsAssessmentUpdate,
    SkillsAssessmentResponse,
    SkillsAssessmentWithItems,
    SkillsAssessmentSummary,
)

__all__ = [
    # Items
    "SkillsAssessmentItemBase",
    "SkillsAssessmentItemResponse",
    # Assessment
    "SkillsAssessmentBase",
    "SkillsAssessmentCreate",
    "SkillsAssessmentUpdate",
    "SkillsAssessmentResponse",
    "SkillsAssessmentWithItems",
    "SkillsAssessmentSummary",
]
