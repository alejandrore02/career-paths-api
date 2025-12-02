"""Evaluation Cycle endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.schemas.evaluation.evaluation import (
    EvaluationCycleCreate,
    EvaluationCycleUpdate,
    EvaluationCycleResponse,
)
from app.services.evaluation_cycle_service import EvaluationCycleService
from app.services.dependencies import get_evaluation_cycle_service

router = APIRouter(
    prefix="/evaluation-cycles", tags=["evaluation-cycles"], redirect_slashes=False
)


@router.post(
    "",
    response_model=EvaluationCycleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Evaluation Cycle",
    description="""
    Create a new evaluation cycle for conducting 360° evaluations.
    
    An evaluation cycle groups multiple individual evaluations into a cohesive
    assessment period (e.g., "2025 Q1", "Annual Review 2025").
    
    **Validation:**
    - End date must be after start date
    - Status must be one of: 'draft', 'active', 'closed'
    - Name is required and must be unique
    
    **Status Flow:**
    - `draft`: Cycle is being configured
    - `active`: Cycle is open for evaluations
    - `closed`: Cycle has ended, no new evaluations allowed
    """,
)
async def create_cycle(
    data: EvaluationCycleCreate,
    service: EvaluationCycleService = Depends(get_evaluation_cycle_service),
) -> EvaluationCycleResponse:
    """
    Create a new evaluation cycle.
    
    Returns:
        Created cycle with generated ID and timestamps
        
    Raises:
        400: Validation error (e.g., invalid dates, invalid status)
    """
    return await service.create_cycle(data)


@router.get(
    "/{cycle_id}",
    response_model=EvaluationCycleResponse,
    summary="Get Evaluation Cycle",
    description="""
    Retrieve a specific evaluation cycle by ID.
    
    Returns full cycle details including dates, status, and metadata.
    """,
)
async def get_cycle(
    cycle_id: UUID,
    service: EvaluationCycleService = Depends(get_evaluation_cycle_service),
) -> EvaluationCycleResponse:
    """
    Get evaluation cycle by ID.
    
    Returns:
        Cycle details
        
    Raises:
        404: Cycle not found
    """
    return await service.get_cycle(cycle_id)


@router.get(
    "",
    response_model=list[EvaluationCycleResponse],
    summary="List Evaluation Cycles",
    description="""
    List all evaluation cycles, optionally filtered by status.
    
    **Filters:**
    - `status`: Filter by cycle status ('draft', 'active', 'closed')
    
    Results are ordered by start date (most recent first).
    """,
)
async def list_cycles(
    status: Optional[str] = Query(
        None, description="Filter by status: 'draft', 'active', or 'closed'"
    ),
    service: EvaluationCycleService = Depends(get_evaluation_cycle_service),
) -> list[EvaluationCycleResponse]:
    """
    List evaluation cycles.
    
    Returns:
        List of cycles (can be empty)
    """
    return await service.list_cycles(status=status)


@router.patch(
    "/{cycle_id}",
    response_model=EvaluationCycleResponse,
    summary="Update Evaluation Cycle",
    description="""
    Update an existing evaluation cycle.
    
    **Common Use Cases:**
    - Close a cycle: `{"status": "closed"}`
    - Reopen a cycle: `{"status": "active"}`
    - Extend deadline: `{"end_date": "2025-12-31"}`
    - Update description: `{"description": "Updated objectives"}`
    
    All fields are optional. Only provided fields will be updated.
    
    **Validation:**
    - End date must remain after start date
    - Status must be valid ('draft', 'active', 'closed')
    """,
)
async def update_cycle(
    cycle_id: UUID,
    data: EvaluationCycleUpdate,
    service: EvaluationCycleService = Depends(get_evaluation_cycle_service),
) -> EvaluationCycleResponse:
    """
    Update evaluation cycle.
    
    Returns:
        Updated cycle
        
    Raises:
        404: Cycle not found
        400: Validation error
    """
    return await service.update_cycle(cycle_id, data)


@router.delete(
    "/{cycle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Evaluation Cycle",
    description="""
    Delete an evaluation cycle.
    
    **IMPORTANT:** Cannot delete cycles that have associated evaluations.
    This prevents data loss and maintains referential integrity.
    
    To remove a cycle with evaluations, first delete all evaluations
    or close the cycle instead.
    """,
)
async def delete_cycle(
    cycle_id: UUID,
    service: EvaluationCycleService = Depends(get_evaluation_cycle_service),
) -> None:
    """
    Delete evaluation cycle.
    
    Raises:
        404: Cycle not found
        400: Cycle has associated evaluations
    """
    await service.delete_cycle(cycle_id)
