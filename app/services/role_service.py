"""
Role service for business logic orchestration.
"""
from typing import Optional
from uuid import UUID

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.core.logging import get_logger
from app.db.models.core import Role
from app.db.unit_of_work import UnitOfWork
from app.schemas.core.role import RoleCreate, RoleUpdate, RoleResponse

logger = get_logger(__name__)


class RoleService:
    """Service for role operations."""

    def __init__(self, uow: UnitOfWork):
        """Initialize service with Unit of Work."""
        self.uow = uow

    async def create_role(self, data: RoleCreate) -> RoleResponse:
        """
        Create a new role.

        Args:
            data: Role creation data

        Returns:
            Created role

        Raises:
            ConflictError: If role name already exists
        """
        # Check name uniqueness
        existing_role = await self.uow.roles.get_by_name(data.name)
        if existing_role:
            raise ConflictError(
                message="Role with this name already exists",
                details={"name": data.name},
            )

        # Create role
        role = Role(
            name=data.name,
            job_family=data.job_family,
            seniority_level=data.seniority_level,
            description=data.description,
            is_active=data.is_active,
        )

        created_role = await self.uow.roles.create(role)
        await self.uow.session.commit()

        logger.info(
            f"Created role: {created_role.name}",
            extra={
                "role_id": str(created_role.id),
                "job_family": created_role.job_family,
                "seniority_level": created_role.seniority_level,
            },
        )

        return RoleResponse.model_validate(created_role)

    async def get_role(self, role_id: UUID) -> RoleResponse:
        """
        Get role by ID.

        Args:
            role_id: Role UUID

        Returns:
            Role details

        Raises:
            NotFoundError: If role not found
        """
        role = await self.uow.roles.get_by_id(role_id)
        if not role:
            raise NotFoundError(
                message="Role not found",
                details={"role_id": str(role_id)},
            )

        return RoleResponse.model_validate(role)

    async def list_roles(
        self,
        active_only: bool = True,
        job_family: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RoleResponse]:
        """
        List roles with optional filters.

        Args:
            active_only: Only return active roles
            job_family: Filter by job family
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of roles
        """
        # Apply specific filters
        if job_family:
            roles = await self.uow.roles.get_by_job_family(job_family, active_only=active_only)
        elif active_only:
            roles = await self.uow.roles.get_all_active(limit=limit, offset=offset)
        else:
            roles = await self.uow.roles.get_all(limit=limit, offset=offset)

        return [RoleResponse.model_validate(r) for r in roles]

    async def update_role(self, role_id: UUID, data: RoleUpdate) -> RoleResponse:
        """
        Update role.

        Args:
            role_id: Role UUID
            data: Update data (partial)

        Returns:
            Updated role

        Raises:
            NotFoundError: If role not found
            ConflictError: If name already exists
        """
        # Get existing role
        role = await self.uow.roles.get_by_id(role_id)
        if not role:
            raise NotFoundError(
                message="Role not found",
                details={"role_id": str(role_id)},
            )

        # Update fields
        update_dict = data.model_dump(exclude_unset=True)

        # Validate name uniqueness
        if "name" in update_dict and update_dict["name"] != role.name:
            existing_role = await self.uow.roles.get_by_name(update_dict["name"])
            if existing_role:
                raise ConflictError(
                    message="Role with this name already exists",
                    details={"name": update_dict["name"]},
                )

        # Apply updates
        for key, value in update_dict.items():
            setattr(role, key, value)

        updated_role = await self.uow.roles.update(role)
        await self.uow.session.commit()

        logger.info(
            f"Updated role: {updated_role.name}",
            extra={"role_id": str(role_id), "updated_fields": list(update_dict.keys())},
        )

        return RoleResponse.model_validate(updated_role)

    async def deactivate_role(self, role_id: UUID) -> RoleResponse:
        """
        Deactivate role (soft delete).

        Args:
            role_id: Role UUID

        Returns:
            Deactivated role

        Raises:
            NotFoundError: If role not found
        """
        role = await self.uow.roles.get_by_id(role_id)
        if not role:
            raise NotFoundError(
                message="Role not found",
                details={"role_id": str(role_id)},
            )

        role.is_active = False
        updated_role = await self.uow.roles.update(role)
        await self.uow.session.commit()

        logger.info(
            f"Deactivated role: {updated_role.name}",
            extra={"role_id": str(role_id)},
        )

        return RoleResponse.model_validate(updated_role)
