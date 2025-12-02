"""
Core schemas for Skill model.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SkillBase(BaseModel):
    """Base Skill schema.
    
    Represents a competency/capability in the organization's skills catalog.
    Skills are evaluated in 360° reviews and tracked for development.
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Skill/competency name (e.g., 'Leadership', 'Python Programming')"
    )
    category: Optional[str] = Field(
        None,
        max_length=100,
        description="Skill category (e.g., 'soft', 'technical', 'leadership')"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the skill and its importance"
    )
    behavioral_indicators: Optional[str] = Field(
        None,
        description="Observable behaviors that demonstrate this skill at different levels"
    )
    is_global: bool = Field(
        True,
        description="Whether this skill is available globally across the organization"
    )
    is_active: bool = Field(
        True,
        description="Whether this skill is currently active in the catalog"
    )


class SkillCreate(SkillBase):
    """Schema for creating a skill.
    
    Inherits all fields from SkillBase.
    Skills should have clear behavioral indicators for evaluation consistency.
    """
    pass


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    behavioral_indicators: Optional[str] = None
    is_global: Optional[bool] = None
    is_active: Optional[bool] = None


class SkillResponse(SkillBase):
    """Skill response schema.
    
    Full skill representation including system-generated fields.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique skill identifier")
    created_at: datetime = Field(..., description="Timestamp when skill was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")
