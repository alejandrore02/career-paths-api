"""
Core schemas for User model.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base User schema.
    
    Represents a collaborator/employee in the talent management system.
    Users are evaluated, have skill profiles, and can progress through career paths.
    """
    
    email: EmailStr = Field(..., description="User's work email address (unique identifier)")
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's full legal or preferred name"
    )
    hire_date: Optional[date] = Field(
        None,
        description="Date the user joined the organization"
    )
    is_active: bool = Field(
        True,
        description="Whether the user is currently active in the system"
    )


class UserCreate(UserBase):
    """Schema for creating a user.
    
    Includes optional organizational hierarchy fields (role, manager).
    """
    
    role_id: Optional[UUID] = Field(
        None,
        description="Current role/position assignment (FK to roles table)"
    )
    manager_id: Optional[UUID] = Field(
        None,
        description="Direct manager/supervisor (FK to users table, self-referential)"
    )


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    hire_date: Optional[date] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema.
    
    Full user representation including system-generated fields.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique user identifier")
    role_id: Optional[UUID] = Field(None, description="Current role assignment")
    manager_id: Optional[UUID] = Field(None, description="Direct manager")
    created_at: datetime = Field(..., description="Timestamp when user was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")


class UserSummary(BaseModel):
    """Condensed user summary.
    
    Lightweight representation for lists, dropdowns, and references.
    Includes only essential identification fields.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str = Field(..., description="User's work email")
    full_name: str = Field(..., description="User's display name")
    is_active: bool = Field(..., description="Active status")
