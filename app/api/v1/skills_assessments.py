"""Skills Assessment endpoints implementing flows.md."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status, Query
from pydantic import BaseModel, Field

from app.schemas.skills_assessment.skills_assessment import (
    SkillsAssessmentResponse,
    SkillsAssessmentWithItems,
)
from app.services.skills_assessment_service import SkillsAssessmentService
from app.services.dependencies import get_skills_assessment_service

router = APIRouter(prefix="/skills-assessments", tags=["skills-assessments"], redirect_slashes=False)


class GenerateAssessmentRequest(BaseModel):
    """Request to generate a skills assessment."""
    user_id: UUID = Field(..., description="User to assess")
    evaluation_cycle_id: UUID = Field(..., description="Evaluation cycle providing 360° data")


@router.post(
    "",
    response_model=SkillsAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI Skills Assessment",
    description="""
    Generate AI Skills Assessment for a user.
    
    This endpoint:
    1. **Step 4:** Build payload from user_skill_scores
       - Retrieves aggregated 360° scores for the cycle
       - Extracts scores by relationship type
       - Adds context: current_position, years_experience
    2. **Step 5:** Call AI Skills Assessment service
       - Sends payload to external AI service
       - Logs request/response in ai_calls_log
       - Handles errors with proper status tracking
    3. **Parse and persist results:**
       - Creates skills_assessments record
       - Creates skills_assessment_items
    
    **Prerequisites:**
    - User must have completed 360° evaluation cycle
    - user_skill_scores must be aggregated (via /evaluations/{id}/process)
    """,
)
async def generate_skills_assessment(
    data: GenerateAssessmentRequest,
    service: SkillsAssessmentService = Depends(get_skills_assessment_service),
) -> SkillsAssessmentResponse:
    """
    Generate AI Skills Assessment.
    Returns:
        Created skills assessment with status='completed'
        
    Raises:
        404: User not found or no skill scores available
        502: AI service error
    """
    assessment = await service.generate_assessment(data.user_id, data.evaluation_cycle_id)
    return assessment


@router.post(
    "/generate",
    response_model=SkillsAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI Skills Assessment (Query Params)",
    description="""
    **DEPRECATED:** Use POST /skills-assessments with body instead.
    
    Generate AI Skills Assessment for a user using query parameters.
    
    This endpoint:
    1. **Step 4:** Build payload from user_skill_scores
       - Retrieves aggregated 360° scores for the cycle
       - Extracts scores by relationship type
       - Adds context: current_position, years_experience
    2. **Step 5:** Call AI Skills Assessment service
       - Sends payload to external AI service
       - Logs request/response in ai_calls_log
       - Handles errors with proper status tracking
    3. **Parse and persist results:**
       - Creates skills_assessments record
       - Creates skills_assessment_items
    
    **Prerequisites:**
    - User must have completed 360° evaluation cycle
    - user_skill_scores must be aggregated (via /evaluations/{id}/process)
    """,
)
async def generate_skills_assessment_legacy(
    user_id: UUID,
    cycle_id: UUID,
    service: SkillsAssessmentService = Depends(get_skills_assessment_service),
) -> SkillsAssessmentResponse:
    """
    Generate AI Skills Assessment.
    Returns:
        Created skills assessment with status='completed'
        
    Raises:
        404: User not found or no skill scores available
        502: AI service error
    """
    assessment = await service.generate_assessment(user_id, cycle_id)
    return assessment


@router.get(
    "/{user_id}/latest",
    response_model=SkillsAssessmentWithItems,
    summary="Get Latest Skills Assessment for User",
    description="""
    Get the most recent completed skills assessment for a user.
    
    Returns:
    - Assessment metadata (status, model info, timestamps)
    - All assessment items grouped by type:
      - Strengths 
      - Growth areas 
      - Hidden talents 
      - Role readiness 
    
    Ordered by most recent processed_at timestamp.
    """,
)
async def get_latest_skills_assessment(
    user_id: UUID,
    service: SkillsAssessmentService = Depends(get_skills_assessment_service),
) -> SkillsAssessmentWithItems:
    """
    Get latest skills assessment for a user.
    
    Returns:
        Latest assessment with all items        
    Raises:
        404: No assessment found for user
    """
    assessment = await service.get_latest_assessment(user_id, include_items=True)
    # Type narrowing: when include_items=True, service returns SkillsAssessmentWithItems
    return assessment  # type: ignore[return-value]


@router.get(
    "/{assessment_id}",
    response_model=SkillsAssessmentWithItems | SkillsAssessmentResponse,
    summary="Get Skills Assessment by ID",
    description="""
    Retrieve a specific skills assessment with all items.
    
    Includes:
    - Full assessment metadata
    - All strengths, growth areas, hidden talents, and role readiness items
    - AI model information and processing details
    """,
)
async def get_skills_assessment(
    assessment_id: UUID,
    include_items: bool = Query(
        True,
        description="Include assessment items (strengths, growth areas, etc.)",
    ),
    service: SkillsAssessmentService = Depends(get_skills_assessment_service),
) -> SkillsAssessmentWithItems | SkillsAssessmentResponse:
    """
    Get skills assessment by ID.        
    Returns:
        Assessment with or without items based on parameter
        
    Raises:
        404: Assessment not found
    """
    assessment = await service.get_assessment_by_id(
        assessment_id,
        include_items=include_items,
    )
    return assessment
