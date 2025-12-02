"""
Skills Assessment schemas aligned with schema.md.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Assessment Item Schemas
class SkillsAssessmentItemBase(BaseModel):
    """Base Skills Assessment Item schema.
    
    Structured output from AI skills assessment analysis.
    Contains detailed insights about strengths, growth areas, hidden talents,
    and role readiness for specific competencies or roles.
    """
    
    item_type: str = Field(
        ...,
        max_length=50,
        description="Item classification: 'strength', 'growth_area', 'hidden_talent', 'role_readiness'"
    )
    label: Optional[str] = Field(
        None,
        max_length=150,
        description="Custom label if skill/role is not in catalog"
    )
    current_level: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Current skill proficiency level (0-10 scale)"
    )
    target_level: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Target/required skill level for development (0-10 scale)"
    )
    gap_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Gap between current and target level (0-10 scale)"
    )
    score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="General score/rating for this item (0-10 scale)"
    )
    priority: Optional[str] = Field(
        None,
        max_length=50,
        description="Development priority: 'Alta', 'Media', 'Baja'"
    )
    readiness_percentage: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Role readiness percentage (0-100, converted from internal 0-1 range)"
    )
    evidence: Optional[str] = Field(
        None,
        description="AI-generated evidence or rationale for this assessment"
    )
    metadata: Optional[dict] = Field(
        None,
        description="Additional metadata from AI analysis",
        validation_alias="item_metadata",  # Maps from DB model attribute
        serialization_alias="metadata"     # Serializes as 'metadata' in response
    )


class SkillsAssessmentItemResponse(SkillsAssessmentItemBase):
    """Skills Assessment Item response schema.
    
    Full structured item with system-generated fields and FK references.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique item identifier")
    skills_assessment_id: UUID = Field(
        ...,
        description="Parent skills assessment ID"
    )
    skill_id: Optional[UUID] = Field(
        None,
        description="Skill ID if item references catalog skill"
    )
    role_id: Optional[UUID] = Field(
        None,
        description="Role ID if item is a role readiness assessment"
    )
    created_at: datetime = Field(..., description="Timestamp when item was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


# Skills Assessment Schemas
class SkillsAssessmentBase(BaseModel):
    """Base Skills Assessment schema.
    
    AI-powered comprehensive skills analysis for a user.
    Aggregates 360° evaluation data and generates structured insights.
    """
    
    status: str = Field(
        ...,
        max_length=30,
        description="Assessment status: 'pending', 'processing', 'completed', 'failed'"
    )
    summary: Optional[str] = Field(
        None,
        description="AI-generated executive summary of the skills profile"
    )


class SkillsAssessmentCreate(BaseModel):
    """Schema for creating a skills assessment (internal use).
    
    Used by the AI service to initiate a new skills assessment job.
    """
    
    user_id: UUID = Field(..., description="User to assess")
    evaluation_cycle_id: Optional[UUID] = Field(
        None,
        description="Evaluation cycle providing input data (if applicable)"
    )
    status: str = Field(
        "pending",
        description="Initial status (typically 'pending' or 'processing')"
    )


class SkillsAssessmentUpdate(BaseModel):
    """Schema for updating a skills assessment.
    
    Used to update assessment status, results, and metadata as AI processing completes.
    """
    
    status: Optional[str] = Field(
        None,
        max_length=30,
        description="Updated status: 'pending', 'processing', 'completed', 'failed'"
    )
    summary: Optional[str] = Field(
        None,
        description="AI-generated executive summary"
    )
    model_name: Optional[str] = Field(
        None,
        max_length=100,
        description="AI model identifier (e.g., 'gpt-4', 'claude-3')"
    )
    model_version: Optional[str] = Field(
        None,
        max_length=50,
        description="AI model version"
    )
    raw_request: Optional[dict] = Field(
        None,
        description="Raw AI request payload (for debugging/audit)"
    )
    raw_response: Optional[dict] = Field(
        None,
        description="Raw AI response payload"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if assessment failed"
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when AI processing completed"
    )


class SkillsAssessmentResponse(SkillsAssessmentBase):
    """Skills Assessment response schema.
    
    Full assessment representation including AI model metadata and timestamps.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique assessment identifier")
    user_id: UUID = Field(..., description="User this assessment is for")
    evaluation_cycle_id: Optional[UUID] = Field(
        None,
        description="Source evaluation cycle (if applicable)"
    )
    model_name: Optional[str] = Field(
        None,
        description="AI model used for analysis"
    )
    model_version: Optional[str] = Field(
        None,
        description="AI model version"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error details if assessment failed"
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="Timestamp of AI processing completion"
    )
    created_at: datetime = Field(..., description="Timestamp when assessment was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


class SkillsAssessmentWithItems(SkillsAssessmentResponse):
    """Skills Assessment response with items included.
    
    Expands assessment with full nested item details (strengths, growth areas, etc.).
    """
    
    items: list[SkillsAssessmentItemResponse] = Field(
        default_factory=list,
        description="All assessment items (strengths, gaps, readiness, etc.)"
    )


class SkillsAssessmentSummary(BaseModel):
    """Condensed skills assessment summary.
    
    Lightweight view with item counts for dashboards and lists.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Assessment identifier")
    user_id: UUID = Field(..., description="User ID")
    status: str = Field(..., description="Assessment status")
    strengths_count: int = Field(
        0,
        description="Number of identified strengths"
    )
    growth_areas_count: int = Field(
        0,
        description="Number of identified growth areas"
    )
    hidden_talents_count: int = Field(
        0,
        description="Number of identified hidden talents"
    )
    role_readiness_count: int = Field(
        0,
        description="Number of role readiness assessments"
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="Processing completion timestamp"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
