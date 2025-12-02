"""
User service for business logic orchestration.
"""
from typing import Optional
from uuid import UUID

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.core.logging import get_logger
from app.db.models.core import User
from app.db.unit_of_work import UnitOfWork
from app.schemas.core.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
)

logger = get_logger(__name__)


class UserService:
    """Service for user operations."""

    def __init__(self, uow: UnitOfWork):
        """Initialize service with Unit of Work."""
        self.uow = uow

    async def create_user(self, data: UserCreate) -> UserResponse:
        """
        Create a new user.

        Args:
            data: User creation data

        Returns:
            Created user

        Raises:
            ConflictError: If email already exists
            NotFoundError: If role_id or manager_id not found
            ValidationError: If validation fails
        """
        # Check email uniqueness
        existing_user = await self.uow.users.get_by_email(data.email)
        if existing_user:
            raise ConflictError(
                message="User with this email already exists",
                details={"email": data.email},
            )

        # Validate role exists
        if data.role_id:
            role = await self.uow.roles.get_by_id(data.role_id)
            if not role:
                raise NotFoundError(
                    message="Role not found",
                    details={"role_id": str(data.role_id)},
                )

        # Validate manager exists
        if data.manager_id:
            manager = await self.uow.users.get_by_id(data.manager_id)
            if not manager:
                raise NotFoundError(
                    message="Manager not found",
                    details={"manager_id": str(data.manager_id)},
                )
            if not manager.is_active:
                raise ValidationError(
                    message="Manager must be an active user",
                    details={"manager_id": str(data.manager_id)},
                )

        # Create user
        user = User(
            email=data.email,
            full_name=data.full_name,
            role_id=data.role_id,
            manager_id=data.manager_id,
            hire_date=data.hire_date,
            is_active=data.is_active,
        )

        created_user = await self.uow.users.create(user)
        await self.uow.session.commit()

        logger.info(
            f"Created user: {created_user.full_name}",
            extra={"user_id": str(created_user.id), "email": created_user.email},
        )

        return UserResponse.model_validate(created_user)

    async def get_user(self, user_id: UUID) -> UserResponse:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User details

        Raises:
            NotFoundError: If user not found
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        return UserResponse.model_validate(user)

    async def list_users(
        self,
        active_only: bool = True,
        role_id: Optional[UUID] = None,
        manager_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserResponse]:
        """
        List users with optional filters.

        Args:
            active_only: Only return active users
            role_id: Filter by role
            manager_id: Filter by manager (direct reports)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of users
        """
        # Apply specific filters
        if role_id:
            users = await self.uow.users.get_by_role_id(role_id, active_only=active_only)
        elif manager_id:
            users = await self.uow.users.get_by_manager_id(
                manager_id, active_only=active_only
            )
        elif active_only:
            users = await self.uow.users.get_active_users(limit=limit, offset=offset)
        else:
            users = await self.uow.users.get_all(limit=limit, offset=offset)

        return [UserResponse.model_validate(u) for u in users]

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        """
        Update user.

        Args:
            user_id: User UUID
            data: Update data (partial)

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            ConflictError: If email already exists
            ValidationError: If validation fails
        """
        # Get existing user
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        # Update fields
        update_dict = data.model_dump(exclude_unset=True)

        # Validate email uniqueness
        if "email" in update_dict and update_dict["email"] != user.email:
            existing_user = await self.uow.users.get_by_email(update_dict["email"])
            if existing_user:
                raise ConflictError(
                    message="User with this email already exists",
                    details={"email": update_dict["email"]},
                )

        # Validate role exists
        if "role_id" in update_dict and update_dict["role_id"]:
            role = await self.uow.roles.get_by_id(update_dict["role_id"])
            if not role:
                raise NotFoundError(
                    message="Role not found",
                    details={"role_id": str(update_dict["role_id"])},
                )

        # Validate manager exists and prevent self-reference
        if "manager_id" in update_dict and update_dict["manager_id"]:
            if update_dict["manager_id"] == user_id:
                raise ValidationError(
                    message="User cannot be their own manager",
                    details={"user_id": str(user_id)},
                )

            manager = await self.uow.users.get_by_id(update_dict["manager_id"])
            if not manager:
                raise NotFoundError(
                    message="Manager not found",
                    details={"manager_id": str(update_dict["manager_id"])},
                )
            if not manager.is_active:
                raise ValidationError(
                    message="Manager must be an active user",
                    details={"manager_id": str(update_dict["manager_id"])},
                )

        # Apply updates
        for key, value in update_dict.items():
            setattr(user, key, value)

        updated_user = await self.uow.users.update(user)
        await self.uow.session.commit()

        logger.info(
            f"Updated user: {updated_user.full_name}",
            extra={"user_id": str(user_id), "updated_fields": list(update_dict.keys())},
        )

        return UserResponse.model_validate(updated_user)

    async def deactivate_user(self, user_id: UUID) -> UserResponse:
        """
        Deactivate user (soft delete).

        Args:
            user_id: User UUID

        Returns:
            Deactivated user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        user.is_active = False
        updated_user = await self.uow.users.update(user)
        await self.uow.session.commit()

        logger.info(
            f"Deactivated user: {updated_user.full_name}",
            extra={"user_id": str(user_id)},
        )

        return UserResponse.model_validate(updated_user)
