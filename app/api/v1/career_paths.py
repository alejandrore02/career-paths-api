
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, Body
from pydantic import BaseModel, Field
from app.services.career_path_service import CareerPathService
from app.services.dependencies import get_career_path_service

from app.schemas.career_path.career_path import (
    CareerPathResponse,
    CareerPathWithSteps,
)

router = APIRouter(prefix="/career-paths", tags=["career-paths"], redirect_slashes=False)


# Request schemas
class GenerateCareerPathRequest(BaseModel):
    """Request schema for generating career paths."""
    
    user_id: UUID = Field(..., description="User to generate career paths for")
    skills_assessment_id: Optional[UUID] = Field(
        None,
        description="Specific skills assessment ID (uses latest if not provided)",
    )
    career_interests: Optional[list[str]] = Field(
        None,
        description="User's stated career interests (e.g., ['leadership', 'technical', 'management'])",
        examples=[["leadership", "management"]],
    )
    time_horizon_years: int = Field(
        3,
        ge=1,
        le=10,
        description="Planning horizon in years (default: 3)",
    )


class GenerateCareerPathsRequest(BaseModel):
    """Request schema for legacy generate endpoint (without user_id in body)."""
    
    skills_assessment_id: Optional[UUID] = Field(
        None,
        description="Specific skills assessment ID (uses latest if not provided)",
    )
    career_interests: Optional[list[str]] = Field(
        None,
        description="User's stated career interests (e.g., ['leadership', 'technical', 'management'])",
        examples=[["leadership", "management"]],
    )
    time_horizon_years: int = Field(
        3,
        ge=1,
        le=10,
        description="Planning horizon in years (default: 3)",
    )


@router.post(
    "",
    response_model=list[CareerPathResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI Career Paths",
    description="""
    Generate AI Career Paths for a user (Flow 1, Steps 6-7 from flows.md).
    
    This endpoint:
    1. **Step 6:** Build payload from skills_assessment
       - Retrieves latest (or specified) skills assessment
       - Gets user's current position from role
       - Builds organization structure (available roles)
       - Adds career interests and time horizon
    2. **Step 7:** Call AI Career Path service
       - Sends payload to external AI service
       - Logs request/response in ai_calls_log
       - Handles errors with proper status tracking
    3. **Parse and persist results:**
       - Creates career_paths records 
       - Creates career_path_steps 
       - Creates development_actions
    
    **Prerequisites:**
    - User must have a completed skills assessment
    - Skills assessment must be based on aggregated 360° data
    """,
)
async def generate_career_paths(
    data: GenerateCareerPathRequest,
    service: CareerPathService = Depends(get_career_path_service),
) -> list[CareerPathResponse]:
    """
    Generate AI Career Paths.
    Returns:
        List of generated career paths
        
    Raises:
        404: User or skills assessment not found
        502: AI service error
    """
    paths = await service.generate_career_paths(
        user_id=data.user_id,
        skills_assessment_id=data.skills_assessment_id,
        career_interests=data.career_interests,
        time_horizon_years=data.time_horizon_years,
    )
    return paths


@router.post(
    "/generate",
    response_model=list[CareerPathResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI Career Paths (Legacy)",
    description="""
    **DEPRECATED:** Use POST /career-paths with body instead.
    
    Generate AI Career Paths for a user (Flow 1, Steps 6-7 from flows.md).
    
    This endpoint:
    1. **Step 6:** Build payload from skills_assessment
       - Retrieves latest (or specified) skills assessment
       - Gets user's current position from role
       - Builds organization structure (available roles)
       - Adds career interests and time horizon
    2. **Step 7:** Call AI Career Path service
       - Sends payload to external AI service
       - Logs request/response in ai_calls_log
       - Handles errors with proper status tracking
    3. **Parse and persist results:**
       - Creates career_paths records 
       - Creates career_path_steps 
       - Creates development_actions
    
    **Prerequisites:**
    - User must have a completed skills assessment
    - Skills assessment must be based on aggregated 360° data
    """,
)
async def generate_career_paths_legacy(
    user_id: UUID,
    request: GenerateCareerPathsRequest = Body(...),
    service: CareerPathService = Depends(get_career_path_service),
) -> list[CareerPathResponse]:
    """
    Generate AI Career Paths.
    Returns:
        List of generated career paths
        
    Raises:
        404: User or skills assessment not found
        502: AI service error
    """
    paths = await service.generate_career_paths(
        user_id=user_id,
        skills_assessment_id=request.skills_assessment_id,
        career_interests=request.career_interests,
        time_horizon_years=request.time_horizon_years,
    )
    return paths


@router.get(
    "/user/{user_id}/recommended",
    response_model=list[CareerPathResponse],
    summary="Get Recommended Career Paths",
    description="""
    Get AI-recommended career paths for a user.
    
    Filters for:
    - `recommended=true` (AI's top picks)
    - Active statuses: proposed, accepted, in_progress
    
    Ordered by feasibility_score (highest first).
    
    Typically returns 1-2 paths that the AI considers most suitable based on:
    - Current skill profile
    - Organization structure
    - Career trajectory analysis
    """,
)
async def get_recommended_career_paths(
    user_id: UUID,
    service: CareerPathService = Depends(get_career_path_service),
) -> list[CareerPathResponse]:
    """
    Get recommended career paths for a user.
    
    Args:
        user_id: User UUID
        service: Injected career path service
        
    Returns:
        List of recommended career paths
    """
    paths = await service.get_recommended_paths(user_id)
    return paths


@router.get(
    "/{user_id}",
    response_model=list[CareerPathResponse],
    summary="Get Career Paths for User",
    description="""
    Get all career paths for a user (Flow 2.1 from flows.md).
    
    Returns paths with optional status filter:
    - `proposed`: AI-generated, not yet accepted by user
    - `accepted`: User has accepted this path as their active development plan
    - `in_progress`: User is actively working on this path
    - `completed`: Path has been completed
    - `discarded`: Path was not chosen or abandoned
    
    Results are ordered by:
    1. Recommended flag (recommended paths first)
    2. Creation date (most recent first)
    """,
)
async def get_career_paths_for_user(
    user_id: UUID,
    status: Optional[str] = Query(
        None,
        description="Filter by status: proposed, accepted, in_progress, completed, discarded",
    ),
    service: CareerPathService = Depends(get_career_path_service),
) -> list[CareerPathResponse]:
    """
    Get career paths for a user.
    Returns:
        List of career paths, optionally filtered by status.
    """
    paths = await service.get_paths_for_user(user_id, status=status)
    return paths


@router.get(
    "/{path_id}/steps",
    response_model=CareerPathWithSteps,
    summary="Get Career Path Steps",
    description="""
    Get detailed career path with all steps and development actions (Flow 2.2 from flows.md).
    
    Returns:
    - Path metadata (name, recommended, feasibility, duration, status)
    - All steps in sequential order:
      - Step number (1, 2, 3, ...)
      - Target role (with FK to roles table)
      - Duration estimate for this step
      - Development actions:
        - Action type (course, project, mentoring, shadowing, certification)
        - Title and description
        - Skill being developed
        - Effort estimate
    
    This is the primary endpoint for displaying a complete career roadmap to users.
    """,
)
async def get_career_path_detail(
    path_id: UUID,
    service: CareerPathService = Depends(get_career_path_service),
) -> CareerPathWithSteps:
    """
    Get detailed career path with steps.
    Returns:
        Career path with nested steps and development actions
    Raises:
        404: Career path not found
    """
    path = await service.get_path_detail(path_id)
    return path


@router.post(
    "/{path_id}/accept",
    response_model=CareerPathResponse,
    summary="Accept Career Path",
    description="""
    Accept a career path as the user's active development plan (Flow 2.3 from flows.md).
    
    This endpoint:
    1. Validates path exists and belongs to user
    2. Validates path status is 'proposed' (can only accept proposed paths)
    3. Marks path as 'accepted'
    4. Marks other proposed/accepted paths for same user as 'discarded'
    5. All updates are atomic (transaction)
    
    **Business Rules:**
    - Only one path can be 'accepted' at a time per user
    - Only paths with status='proposed' can be accepted
    - Accepting a path automatically discards alternatives
    
    **Status Transitions:**
    - `proposed` → `accepted` (this path)
    - `proposed` → `discarded` (other paths)
    - `accepted` → `discarded` (previously accepted path, if any)
    """,
)
async def accept_career_path(
    path_id: UUID,
    user_id: UUID,
    service: CareerPathService = Depends(get_career_path_service),
) -> CareerPathResponse:
    """
    Accept a career path.
    Returns:
        Accepted career path
        
    Raises:
        404: Career path not found
        403: Path doesn't belong to user
        409: Path status doesn't allow acceptance
    """
    path = await service.accept_path(path_id, user_id)
    return path
