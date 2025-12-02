"""Evaluation endpoints implementing flows.md."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.schemas.evaluation.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationWithScores,
    UserSkillProfile,
)
from app.services.evaluation_service import EvaluationService
from app.services.dependencies import get_evaluation_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"], redirect_slashes=False)


@router.post(
    "",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create 360° Evaluation",
    description="""
    Create a new 360° evaluation.
    
    This endpoint:
    - Validates user, evaluator, and evaluation cycle exist
    - Ensures cycle is active
    - Normalizes competency names to skill_ids from catalog
    - Creates evaluation with status='submitted'
    - Creates associated competency scores
    
    **Competency Scores:**
    - Score range: 0.0-10.0
    - At least one competency required
    - Competency names must exist in skills catalog
    """,
)
async def create_evaluation(
    data: EvaluationCreate,
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationResponse:
    """
    Create a new 360° evaluation.    
    Returns:
        Created evaluation with status='submitted'
        
    Raises:
        404: User, evaluator, or cycle not found
        400: Invalid data (e.g., competency not in catalog, score out of range)
        409: Cycle not active
    """
    evaluation = await service.create_evaluation(data)
    return evaluation


@router.get(
    "",
    response_model=list[EvaluationResponse],
    summary="List Evaluations",
    description="""
    List evaluations with optional filters.
    
    **Filters:**
    - `user_id`: Filter by user being evaluated
    - `evaluator_id`: Filter by evaluator
    - `cycle_id`: Filter by evaluation cycle
    - `status`: Filter by status ('submitted', 'draft')
    - `limit`: Maximum results (default: 100, max: 1000)
    - `offset`: Pagination offset (default: 0)
    
    Results are ordered by creation date (most recent first).
    """,
)
async def list_evaluations(
    user_id: Optional[UUID] = Query(None, description="Filter by user being evaluated"),
    evaluator_id: Optional[UUID] = Query(None, description="Filter by evaluator"),
    cycle_id: Optional[UUID] = Query(None, description="Filter by evaluation cycle"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: EvaluationService = Depends(get_evaluation_service),
) -> list[EvaluationResponse]:
    """
    List evaluations with filters.
    
    Returns:
        List of evaluations (can be empty)
    """
    return await service.list_evaluations(
        user_id=user_id,
        evaluator_id=evaluator_id,
        cycle_id=cycle_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationWithScores,
    summary="Get Evaluation by ID",
    description="""
    Retrieve a specific evaluation with all competency scores.
    
    Returns detailed evaluation including:
    - Evaluation metadata (user, evaluator, cycle, relationship, status)
    - All competency scores with comments
    - Timestamps
    """,
)
async def get_evaluation(
    evaluation_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationWithScores:
    """
    Get evaluation by ID with scores.

        
    Returns:
        Evaluation with nested competency scores
        
    Raises:
        404: Evaluation not found
    """
    evaluation = await service.get_evaluation(evaluation_id, include_scores=True)
    # Type narrowing: when include_scores=True, service returns EvaluationWithScores
    return evaluation  # type: ignore[return-value]


@router.post(
    "/{evaluation_id}/process",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process Evaluation and Trigger AI Workflows",
    description="""
    Process evaluation and trigger AI workflows.
    
    This endpoint orchestrates:
    1. **Step 2:** Detect if 360° cycle is complete for user
       - Validates ≥1 self, ≥1 manager, ≥2 peers (configurable)
    2. **Step 3:** Aggregate scores into user_skill_scores
       - Calculates overall avg, avg by relationship, confidence
       - Stores raw stats in JSONB
    3. **Steps 4-5:** Trigger AI Skills Assessment (future)
    4. **Steps 6-7:** Trigger AI Career Path generation (future)
    
    **Returns 202 Accepted** as processing may continue asynchronously.
    
    **Cycle Completion Rules:**
    - Must have at least 1 self-evaluation
    - Must have at least 1 manager evaluation
    - Must have at least 2 peer evaluations (default)
    - Must have at least 0 direct report evaluations (default)
    - Only evaluations with status='submitted' are counted
    """,
)
async def process_evaluation(
    evaluation_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service),
) -> dict:
    """
    Process evaluation and check for cycle completion.
        
    Returns:
        Processing result with cycle completion status
        
    Raises:
        404: Evaluation not found
        409: Cycle not complete (missing required evaluations)
    """
    result = await service.process_evaluation(evaluation_id)
    return result


@router.get(
    "/user/{user_id}/cycle/{cycle_id}/profile",
    response_model=UserSkillProfile,
    summary="Get User Skill Profile for Cycle",
    description="""
    Get aggregated skill profile for a user in a specific evaluation cycle.
    
    Returns consolidated skill scores derived from 360° evaluations:
    - Overall average score per skill
    - Confidence level (0-1) based on number of evaluations
    - Raw statistics (averages by relationship, n counts, etc.)
    
    This data is generated after cycle completion (Step 3 in flows.md).
    """,
)
async def get_user_skill_profile(
    user_id: UUID,
    cycle_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service),
) -> UserSkillProfile:
    """
    Get aggregated skill profile for user in cycle.
    Returns:
        Aggregated skill profile with scores, confidence, and stats
    """
    profile = await service.get_user_skill_profile(user_id, cycle_id)
    return profile
