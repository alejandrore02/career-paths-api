"""AI Skills Assessment models."""

from app.db.models.skills_assessment.skills_assessment import SkillsAssessment
from app.db.models.skills_assessment.skills_assessment_item import SkillsAssessmentItem

__all__ = [
    "SkillsAssessment",
    "SkillsAssessmentItem",
]
