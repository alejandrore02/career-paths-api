"""
Career Path schemas aligned with schema.md.
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Development Action Schemas
class DevelopmentActionBase(BaseModel):
    """Base Development Action schema.
    
    Recommended development activity to build specific skills.
    Can be courses, projects, mentoring, or other learning experiences.
    """
    
    action_type: str = Field(
        ...,
        max_length=50,
        description="Action type: 'course', 'project', 'mentoring', 'shadowing', 'certification'"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Descriptive title of the development action"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the action and learning objectives"
    )
    provider: Optional[str] = Field(
        None,
        max_length=200,
        description="Provider/platform offering this action (e.g., Coursera, internal L&D)"
    )
    url: Optional[str] = Field(
        None,
        max_length=500,
        description="Link to resource or enrollment page"
    )
    estimated_effort_hours: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated time investment in hours"
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional metadata (cost, prerequisites, etc.)",
        validation_alias="action_metadata",  # Maps from DB model attribute
        serialization_alias="metadata"       # Serializes as 'metadata' in response
    )


class DevelopmentActionResponse(DevelopmentActionBase):
    """Development Action response schema.
    
    Full action representation with system-generated fields and FK references.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique action identifier")
    career_path_step_id: UUID = Field(
        ...,
        description="Parent career path step this action belongs to"
    )
    skill_id: Optional[UUID] = Field(
        None,
        description="Skill this action helps develop (if applicable)"
    )
    created_at: datetime = Field(..., description="Timestamp when action was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


# Career Path Step Schemas
class CareerPathStepBase(BaseModel):
    """Base Career Path Step schema.
    
    Individual milestone or stage within a career development path.
    Represents progression from one role/level to another.
    """
    
    step_number: int = Field(
        ...,
        ge=1,
        description="Sequential order of this step in the path (1-based)"
    )
    step_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Descriptive name for this step/milestone"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of activities and goals for this step"
    )
    duration_months: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated duration to complete this step (in months)"
    )
    metadata: Optional[dict] = Field(
        None,
        description="Additional metadata (skills to develop, milestones, etc.)",
        validation_alias="step_metadata",  # Maps from DB model attribute
        serialization_alias="metadata"     # Serializes as 'metadata' in response
    )


class CareerPathStepResponse(CareerPathStepBase):
    """Career Path Step response schema.
    
    Full step representation with system-generated fields and FK references.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique step identifier")
    career_path_id: UUID = Field(
        ...,
        description="Parent career path this step belongs to"
    )
    target_role_id: Optional[UUID] = Field(
        None,
        description="Target role for this step (if applicable)"
    )
    created_at: datetime = Field(..., description="Timestamp when step was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


class CareerPathStepWithActions(CareerPathStepResponse):
    """Career Path Step with development actions included.
    
    Expands step with nested development actions for complete view.
    """
    
    development_actions: list[DevelopmentActionResponse] = Field(
        default_factory=list,
        description="Recommended development actions for this step"
    )


# Career Path Schemas
class CareerPathBase(BaseModel):
    """Base Career Path schema.
    
    AI-generated career development route for a user.
    Represents progression paths with feasibility estimates and multi-step journeys.
    """
    
    path_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Descriptive name for this career path"
    )
    recommended: bool = Field(
        False,
        description="Whether this is the AI-recommended primary path"
    )
    feasibility_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Path feasibility probability (0-1 range, where 1=highly feasible)"
    )
    total_duration_months: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated total duration to complete this path (in months)"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes or context about this path"
    )


class CareerPathCreate(BaseModel):
    """Schema for creating a career path (internal use).
    
    Used by AI service to create new career path recommendations.
    """
    
    user_id: UUID = Field(..., description="User this path is designed for")
    skills_assessment_id: Optional[UUID] = Field(
        None,
        description="Associated skills assessment that informed this path"
    )
    path_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Descriptive name for this career path"
    )
    recommended: bool = Field(
        False,
        description="Whether this is the AI-recommended primary path"
    )
    feasibility_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Path feasibility probability (0-1 range)"
    )
    total_duration_months: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated total duration (months)"
    )
    status: str = Field(
        "proposed",
        description="Initial status: 'proposed', 'accepted', 'in_progress', 'completed', 'discarded'"
    )
    ai_metadata: Optional[dict] = Field(
        None,
        description="AI model metadata (model name, version, confidence, etc.)"
    )
    notes: Optional[str] = Field(None, description="Additional notes")


class CareerPathUpdate(BaseModel):
    """Schema for updating a career path.
    
    Allows users or admins to modify path details or status.
    """
    
    path_name: Optional[str] = Field(None, min_length=1, max_length=200)
    recommended: Optional[bool] = None
    feasibility_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Path feasibility probability (0-1 range)"
    )
    total_duration_months: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(
        None,
        max_length=30,
        description="Path status: 'proposed', 'accepted', 'in_progress', 'completed', 'discarded'"
    )
    notes: Optional[str] = None


class CareerPathResponse(CareerPathBase):
    """Career Path response schema.
    
    Full path representation including status, AI metadata, and timestamps.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique path identifier")
    user_id: UUID = Field(..., description="User this path is designed for")
    skills_assessment_id: Optional[UUID] = Field(
        None,
        description="Source skills assessment that informed this path"
    )
    status: str = Field(
        ...,
        description="Path status: 'proposed', 'accepted', 'in_progress', 'completed', 'discarded'"
    )
    ai_metadata: Optional[dict] = Field(
        None,
        description="AI model metadata (model, version, confidence, etc.)"
    )
    created_at: datetime = Field(..., description="Timestamp when path was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


class CareerPathWithSteps(CareerPathResponse):
    """Career Path with steps and actions included.
    
    Complete nested view of entire career path with all steps and development actions.
    """
    
    steps: list[CareerPathStepWithActions] = Field(
        default_factory=list,
        description="All steps in this career path (ordered by step_number)"
    )


class CareerPathSummary(BaseModel):
    """Condensed career path summary.
    
    Lightweight view for dashboards, lists, and user selections.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Path identifier")
    user_id: UUID = Field(..., description="User ID")
    path_name: str = Field(..., description="Path name")
    recommended: bool = Field(..., description="Is this the recommended path?")
    status: str = Field(..., description="Path status")
    total_duration_months: Optional[int] = Field(
        None,
        description="Total estimated duration"
    )
    feasibility_score: Optional[float] = Field(
        None,
        description="Feasibility score (0-1)"
    )
    steps_count: int = Field(
        0,
        description="Number of steps in this path"
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class AcceptCareerPathRequest(BaseModel):
    """Request to accept a career path.
    
    User action to formally accept/commit to a proposed career path.
    """
    
    notes: Optional[str] = Field(
        None,
        description="Optional notes or commitment statement from user"
    )
