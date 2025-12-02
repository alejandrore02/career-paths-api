"""
Evaluation schemas aligned with schema.md.
"""
from datetime import date, datetime
from typing import Optional, Protocol, Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Evaluation Cycle Schemas
class EvaluationCycleBase(BaseModel):
    """Base Evaluation Cycle schema.
    
    Represents a campaign/period for conducting 360° evaluations.
    Groups multiple individual evaluations into a cohesive assessment cycle.
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Cycle name/identifier (e.g., '360 2025 Q1', 'Annual Review 2025')"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of cycle objectives and scope"
    )
    start_date: date = Field(..., description="Cycle start date")
    end_date: date = Field(..., description="Cycle end date")
    status: str = Field(
        ...,
        max_length=30,
        description="Cycle status: 'draft', 'active', 'closed'"
    )


class EvaluationCycleCreate(EvaluationCycleBase):
    """Schema for creating an evaluation cycle.
    
    Optionally tracks who created the cycle for audit purposes.
    """
    
    created_by: Optional[UUID] = Field(
        None,
        description="User ID of the admin/manager who created this cycle"
    )


class EvaluationCycleUpdate(BaseModel):
    """Schema for updating an evaluation cycle."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=30)


class EvaluationCycleResponse(EvaluationCycleBase):
    """Evaluation Cycle response schema.
    
    Full cycle representation including system-generated fields.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique cycle identifier")
    created_by: Optional[UUID] = Field(None, description="Creator user ID")
    created_at: datetime = Field(..., description="Timestamp when cycle was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


# Competency Score Schemas
class CompetencyScoreBase(BaseModel):
    """Base Competency Score schema.
    
    Represents an individual skill rating within a 360° evaluation.
    Scores follow the standard competency scale (0.0-10.0).
    """
    
    competency_name: str = Field(
        ...,
        description="Name of the competency/skill being evaluated"
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Competency score on 0-10 scale (0=no evidence, 10=mastery)"
    )
    comments: Optional[str] = Field(
        None,
        description="Optional qualitative feedback or justification for the score"
    )


class CompetencyScoreCreate(CompetencyScoreBase):
    """Schema for creating a competency score (used in evaluation creation)."""
    pass



class CompetencyScoreResponse(BaseModel):
    """Competency Score response schema.
    
    Individual skill rating within a 360° evaluation, including full metadata.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique score identifier")
    evaluation_id: UUID = Field(..., description="Parent evaluation ID")
    skill_id: UUID = Field(..., description="Skill/competency being rated")
    score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Competency score on 0-10 scale"
    )
    comments: Optional[str] = Field(
        None,
        description="Evaluator's qualitative feedback"
    )
    created_at: datetime = Field(..., description="Timestamp when score was recorded")
    updated_at: datetime = Field(..., description="Timestamp of last update")


# Evaluation Schemas
class EvaluationBase(BaseModel):
    """Base Evaluation schema.
    
    Represents a single 360° evaluation: one evaluator assessing one user.
    """
    
    evaluator_relationship: str = Field(
        ...,
        max_length=30,
        description="Relationship type: 'self', 'peer', 'manager', 'direct_report'"
    )


class EvaluationCreate(EvaluationBase):
    """Schema for creating an evaluation.
    
    Includes the user being evaluated, the evaluator, and their competency ratings.
    """
    
    user_id: UUID = Field(
        ...,
        description="User being evaluated (the 'subject' of the evaluation)"
    )
    evaluation_cycle_id: UUID = Field(
        ...,
        description="Evaluation cycle this evaluation belongs to"
    )
    evaluator_id: UUID = Field(
        ...,
        description="User performing the evaluation (the 'rater')"
    )
    competencies: list[CompetencyScoreCreate] = Field(
        ...,
        min_length=1,
        description="List of competency scores (at least one required)"
    )


class EvaluationUpdate(BaseModel):
    """Schema for updating an evaluation."""
    
    status: Optional[str] = Field(None, max_length=30)  # pending, submitted, cancelled


class EvaluationResponse(EvaluationBase):
    """Evaluation response schema.
    
    Full evaluation representation including status and timestamps.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique evaluation identifier")
    user_id: UUID = Field(..., description="User being evaluated")
    evaluation_cycle_id: UUID = Field(..., description="Evaluation cycle ID")
    evaluator_id: UUID = Field(..., description="Evaluator user ID")
    status: str = Field(
        ...,
        description="Evaluation status: 'pending', 'submitted', 'cancelled'"
    )
    submitted_at: Optional[datetime] = Field(
        None,
        description="Timestamp when evaluation was submitted (null if pending)"
    )
    created_at: datetime = Field(..., description="Timestamp when evaluation was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


class EvaluationWithScores(EvaluationResponse):
    """Evaluation response with competency scores included.
    
    Expands the evaluation with full nested competency score details.
    Useful for displaying complete evaluation results.
    """
    
    competency_scores: list[CompetencyScoreResponse] = Field(
        default_factory=list,
        description="All competency scores for this evaluation"
    )


# User Skill Score Schemas (Aggregated Profile)
class UserSkillScoreResponse(BaseModel):
    """User Skill Score response schema (aggregated from 360°).
    
    Consolidated skill profile derived from multiple evaluations.
    Aggregates scores from different evaluator relationships (self, peer, manager, direct_report).
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID = Field(..., description="User being assessed")
    evaluation_cycle_id: UUID = Field(..., description="Evaluation cycle this score belongs to")
    skill_id: UUID = Field(..., description="Skill/competency being scored")
    source: str = Field(
        ...,
        description="Aggregation source: '360_aggregated', 'self_only', 'manager_only', etc."
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Aggregated skill score on 0-10 scale"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Statistical confidence in the aggregated score (0-1 range)"
    )
    raw_stats: Optional[dict] = Field(
        None,
        description="Raw statistical data: {mean, std, n, etc.}"
    )
    created_at: datetime
    updated_at: datetime


class UserSkillProfile(BaseModel):
    """Aggregated skill profile for a user in a cycle.
    
    Consolidated view of all skill scores for a user in an evaluation cycle.
    Includes computed properties for analytics.
    """
    
    user_id: UUID = Field(..., description="User this profile belongs to")
    evaluation_cycle_id: UUID = Field(..., description="Evaluation cycle")
    skill_scores: list[UserSkillScoreResponse] = Field(
        default_factory=list,
        description="All aggregated skill scores for this user/cycle"
    )
    
    @property
    def total_skills(self) -> int:
        """Total number of skills in profile."""
        return len(self.skill_scores)
    
    @property
    def avg_score(self) -> Optional[float]:
        """Average score across all skills. Not so relevant if because maybe the competency set is not comparable."""
        if not self.skill_scores:
            return None
        return sum(s.score for s in self.skill_scores) / len(self.skill_scores)
