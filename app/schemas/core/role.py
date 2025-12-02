"""
Core schemas for Role model.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """Base Role schema.
    
    Represents a job position/title in the organization.
    Roles have skill requirements and serve as targets for career paths.
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Role title (e.g., 'Store Manager', 'Senior Developer')"
    )
    job_family: Optional[str] = Field(
        None,
        max_length=100,
        description="Broad job category (e.g., 'Operations', 'Sales', 'Engineering')"
    )
    seniority_level: Optional[str] = Field(
        None,
        max_length=50,
        description="Career level (e.g., 'Junior', 'Mid', 'Senior', 'Director')"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed role description, responsibilities, and expectations"
    )
    is_active: bool = Field(
        True,
        description="Whether this role is currently active/available"
    )


class RoleCreate(RoleBase):
    """Schema for creating a role.
    
    Inherits all fields from RoleBase.
    Skill requirements can be added separately via role_skill_requirements.
    """
    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    job_family: Optional[str] = Field(None, max_length=100)
    seniority_level: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    """Role response schema.
    
    Full role representation including system-generated fields.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique role identifier")
    created_at: datetime = Field(..., description="Timestamp when role was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")
