"""User endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.schemas.core.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.services.dependencies import get_user_service

router = APIRouter(prefix="/users", tags=["users"], redirect_slashes=False)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="""
    Create a new user in the talent management system.
    
    Users represent employees/collaborators who can:
    - Be evaluated in 360° cycles
    - Have managers and direct reports
    - Be assigned to roles with skill requirements
    - Progress through career paths
    
    **Validation:**
    - Email must be unique
    - Role and manager (if provided) must exist
    - Manager must be an active user
    """,
)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Create a new user.
    
    Returns:
        Created user with generated ID and timestamps
        
    Raises:
        400: Validation error
        404: Role or manager not found
        409: Email already exists
    """
    return await service.create_user(data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User",
    description="""
    Retrieve a specific user by ID.
    
    Returns full user details including role and manager assignments.
    """,
)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Get user by ID.
    
    Returns:
        User details
        
    Raises:
        404: User not found
    """
    return await service.get_user(user_id)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List Users",
    description="""
    List users with optional filters.
    
    **Filters:**
    - `active_only`: Show only active users (default: true)
    - `role_id`: Filter by role assignment
    - `manager_id`: Get direct reports of a manager
    - `limit`: Maximum results (default: 100, max: 1000)
    - `offset`: Pagination offset (default: 0)
    
    Results are ordered alphabetically by full name.
    """,
)
async def list_users(
    active_only: bool = Query(True, description="Filter by active status"),
    role_id: Optional[UUID] = Query(None, description="Filter by role"),
    manager_id: Optional[UUID] = Query(None, description="Filter by manager (direct reports)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """
    List users with filters.
    
    Returns:
        List of users (can be empty)
    """
    return await service.list_users(
        active_only=active_only,
        role_id=role_id,
        manager_id=manager_id,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="""
    Update an existing user.
    
    **Common Use Cases:**
    - Change role: `{"role_id": "uuid"}`
    - Assign manager: `{"manager_id": "uuid"}`
    - Update email: `{"email": "new@example.com"}`
    - Deactivate: `{"is_active": false}` (or use DELETE endpoint)
    
    All fields are optional. Only provided fields will be updated.
    
    **Validation:**
    - Email must remain unique
    - Role and manager (if provided) must exist
    - User cannot be their own manager
    """,
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Update user.
    
    Returns:
        Updated user
        
    Raises:
        404: User, role, or manager not found
        400: Validation error (e.g., self-reference)
        409: Email already exists
    """
    return await service.update_user(user_id, data)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="Deactivate User",
    description="""
    Deactivate a user (soft delete).
    
    Sets `is_active = false` instead of removing the record.
    This preserves historical data (evaluations, assessments, career paths).
    
    **Note:** This is a soft delete. The user record remains in the database
    but will be filtered out of active user lists by default.
    """,
)
async def deactivate_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Deactivate user (soft delete).
    
    Returns:
        Deactivated user with is_active=false
        
    Raises:
        404: User not found
    """
    return await service.deactivate_user(user_id)
