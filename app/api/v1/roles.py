"""Role endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.schemas.core.role import RoleCreate, RoleUpdate, RoleResponse
from app.services.role_service import RoleService
from app.services.dependencies import get_role_service

router = APIRouter(prefix="/roles", tags=["roles"], redirect_slashes=False)


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Role",
    description="""
    Create a new role (job position/title) in the organization.
    
    Roles represent positions that:
    - Users can be assigned to
    - Have specific skill requirements
    - Serve as targets for career path progression
    - Define organizational hierarchy and progression paths
    
    **Best Practices:**
    - Use consistent naming (e.g., "Store Manager", "Senior Developer")
    - Assign `job_family` for grouping related roles
    - Set `seniority_level` for career progression clarity
    - Provide detailed descriptions for expectations
    
    **Validation:**
    - Role name must be unique
    """,
)
async def create_role(
    data: RoleCreate,
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    """
    Create a new role.
    
    Returns:
        Created role with generated ID and timestamps
        
    Raises:
        409: Role name already exists
    """
    return await service.create_role(data)


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get Role",
    description="""
    Retrieve a specific role by ID.
    
    Returns full role details including job family, seniority level, and description.
    """,
)
async def get_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    """
    Get role by ID.
    
    Returns:
        Role details
        
    Raises:
        404: Role not found
    """
    return await service.get_role(role_id)


@router.get(
    "",
    response_model=list[RoleResponse],
    summary="List Roles",
    description="""
    List organizational roles with optional filters.
    
    **Filters:**
    - `active_only`: Show only active roles (default: true)
    - `job_family`: Filter by job family (e.g., 'Operations', 'Sales')
    - `limit`: Maximum results (default: 100, max: 1000)
    - `offset`: Pagination offset (default: 0)
    
    Results are ordered alphabetically by role name (and seniority when filtering by job_family).
    
    **Use Cases:**
    - Display career progression paths within a job family
    - Populate role selection dropdowns for user assignment
    - Browse available positions for career planning
    """,
)
async def list_roles(
    active_only: bool = Query(True, description="Filter by active status"),
    job_family: Optional[str] = Query(None, description="Filter by job family"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: RoleService = Depends(get_role_service),
) -> list[RoleResponse]:
    """
    List roles with filters.
    
    Returns:
        List of roles (can be empty)
    """
    return await service.list_roles(
        active_only=active_only,
        job_family=job_family,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update Role",
    description="""
    Update an existing role.
    
    **Common Use Cases:**
    - Update description: `{"description": "Enhanced responsibilities..."}`
    - Change seniority level: `{"seniority_level": "Senior"}`
    - Update job family: `{"job_family": "Engineering"}`
    - Deactivate: `{"is_active": false}` (or use DELETE endpoint)
    
    All fields are optional. Only provided fields will be updated.
    
    **Validation:**
    - Role name must remain unique
    """,
)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    """
    Update role.
    
    Returns:
        Updated role
        
    Raises:
        404: Role not found
        409: Role name already exists
    """
    return await service.update_role(role_id, data)


@router.delete(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Deactivate Role",
    description="""
    Deactivate a role (soft delete).
    
    Sets `is_active = false` instead of removing the record.
    This preserves historical data (user assignments, career paths) while
    removing the role from active catalogs.
    
    **Note:** Deactivated roles will not appear in:
    - User assignment dropdowns (by default)
    - Career path recommendations
    - Active role listings
    
    Users currently assigned to this role retain their assignment.
    Historical data using this role remains intact.
    """,
)
async def deactivate_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    """
    Deactivate role (soft delete).
    
    Returns:
        Deactivated role with is_active=false
        
    Raises:
        404: Role not found
    """
    return await service.deactivate_role(role_id)
