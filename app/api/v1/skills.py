"""Skill endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.schemas.core.skill import SkillCreate, SkillUpdate, SkillResponse
from app.services.skill_service import SkillService
from app.services.dependencies import get_skill_service

router = APIRouter(prefix="/skills", tags=["skills"], redirect_slashes=False)


@router.post(
    "",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Skill",
    description="""
    Create a new skill in the organization's competency catalog.
    
    Skills represent competencies/capabilities that are:
    - Evaluated in 360° reviews
    - Tracked for employee development
    - Required for specific roles
    - Assessed by AI for career path recommendations
    
    **Best Practices:**
    - Provide clear behavioral indicators for consistent evaluation
    - Use categories to organize skills (e.g., 'technical', 'leadership', 'soft')
    - Mark as `is_global=true` for organization-wide skills
    
    **Validation:**
    - Skill name must be unique
    """,
)
async def create_skill(
    data: SkillCreate,
    service: SkillService = Depends(get_skill_service),
) -> SkillResponse:
    """
    Create a new skill.
    
    Returns:
        Created skill with generated ID and timestamps
        
    Raises:
        409: Skill name already exists
    """
    return await service.create_skill(data)


@router.get(
    "/{skill_id}",
    response_model=SkillResponse,
    summary="Get Skill",
    description="""
    Retrieve a specific skill by ID.
    
    Returns full skill details including behavioral indicators and categorization.
    """,
)
async def get_skill(
    skill_id: UUID,
    service: SkillService = Depends(get_skill_service),
) -> SkillResponse:
    """
    Get skill by ID.
    
    Returns:
        Skill details
        
    Raises:
        404: Skill not found
    """
    return await service.get_skill(skill_id)


@router.get(
    "",
    response_model=list[SkillResponse],
    summary="List Skills",
    description="""
    List skills from the organization's competency catalog.
    
    **Filters:**
    - `active_only`: Show only active skills (default: true)
    - `category`: Filter by category (e.g., 'technical', 'leadership', 'soft')
    - `global_only`: Only return global skills (default: false)
    - `limit`: Maximum results (default: 100, max: 1000)
    - `offset`: Pagination offset (default: 0)
    
    Results are ordered alphabetically by skill name.
    
    **Use Cases:**
    - Populate skill selection dropdowns in evaluation forms
    - Browse available competencies for development planning
    - Filter skills by category for targeted assessments
    """,
)
async def list_skills(
    active_only: bool = Query(True, description="Filter by active status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    global_only: bool = Query(False, description="Only return global skills"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: SkillService = Depends(get_skill_service),
) -> list[SkillResponse]:
    """
    List skills with filters.
    
    Returns:
        List of skills (can be empty)
    """
    return await service.list_skills(
        active_only=active_only,
        category=category,
        global_only=global_only,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{skill_id}",
    response_model=SkillResponse,
    summary="Update Skill",
    description="""
    Update an existing skill.
    
    **Common Use Cases:**
    - Update description: `{"description": "Enhanced definition..."}`
    - Change category: `{"category": "leadership"}`
    - Update behavioral indicators: `{"behavioral_indicators": "..."}`
    - Deactivate: `{"is_active": false}` (or use DELETE endpoint)
    
    All fields are optional. Only provided fields will be updated.
    
    **Validation:**
    - Skill name must remain unique
    """,
)
async def update_skill(
    skill_id: UUID,
    data: SkillUpdate,
    service: SkillService = Depends(get_skill_service),
) -> SkillResponse:
    """
    Update skill.
    
    Returns:
        Updated skill
        
    Raises:
        404: Skill not found
        409: Skill name already exists
    """
    return await service.update_skill(skill_id, data)


@router.delete(
    "/{skill_id}",
    response_model=SkillResponse,
    summary="Deactivate Skill",
    description="""
    Deactivate a skill (soft delete).
    
    Sets `is_active = false` instead of removing the record.
    This preserves historical data (evaluations, assessments) while
    removing the skill from active catalogs.
    
    **Note:** Deactivated skills will not appear in:
    - Evaluation form dropdowns (by default)
    - Role skill requirements (by default)
    - Career path recommendations
    
    Historical data using this skill remains intact.
    """,
)
async def deactivate_skill(
    skill_id: UUID,
    service: SkillService = Depends(get_skill_service),
) -> SkillResponse:
    """
    Deactivate skill (soft delete).
    
    Returns:
        Deactivated skill with is_active=false
        
    Raises:
        404: Skill not found
    """
    return await service.deactivate_skill(skill_id)
