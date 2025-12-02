"""
Evaluation Cycle service for business logic orchestration.
"""
from typing import Optional
from uuid import UUID

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models.evaluation import EvaluationCycle
from app.db.unit_of_work import UnitOfWork
from app.schemas.evaluation.evaluation import (
    EvaluationCycleCreate,
    EvaluationCycleUpdate,
    EvaluationCycleResponse,
)

logger = get_logger(__name__)


class EvaluationCycleService:
    """Service for evaluation cycle operations."""

    def __init__(self, uow: UnitOfWork):
        """Initialize service with Unit of Work."""
        self.uow = uow

    async def create_cycle(
        self, data: EvaluationCycleCreate
    ) -> EvaluationCycleResponse:
        """
        Create a new evaluation cycle.

        Args:
            data: Cycle creation data

        Returns:
            Created cycle

        Raises:
            ValidationError: If validation fails (e.g., end_date < start_date)
        """
        # Validate dates
        if data.end_date < data.start_date:
            raise ValidationError(
                message="End date must be after start date",
                details={"start_date": str(data.start_date), "end_date": str(data.end_date)},
            )

        # Validate status
        valid_statuses = {"draft", "active", "closed"}
        if data.status not in valid_statuses:
            raise ValidationError(
                message=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                details={"status": data.status, "valid_statuses": list(valid_statuses)},
            )

        # Create cycle
        cycle = EvaluationCycle(
            name=data.name,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status,
            created_by=data.created_by,
        )

        created_cycle = await self.uow.evaluation_cycles.create(cycle)
        await self.uow.session.commit()

        logger.info(
            f"Created evaluation cycle: {created_cycle.name}",
            extra={"cycle_id": str(created_cycle.id), "status": created_cycle.status},
        )

        return EvaluationCycleResponse.model_validate(created_cycle)

    async def get_cycle(self, cycle_id: UUID) -> EvaluationCycleResponse:
        """
        Get evaluation cycle by ID.

        Args:
            cycle_id: Cycle UUID

        Returns:
            Cycle details

        Raises:
            NotFoundError: If cycle not found
        """
        cycle = await self.uow.evaluation_cycles.get_by_id(cycle_id)
        if not cycle:
            raise NotFoundError(
                message="Evaluation cycle not found",
                details={"cycle_id": str(cycle_id)},
            )

        return EvaluationCycleResponse.model_validate(cycle)

    async def list_cycles(
        self, status: Optional[str] = None
    ) -> list[EvaluationCycleResponse]:
        """
        List all evaluation cycles, optionally filtered by status.

        Args:
            status: Optional status filter ('active', 'draft', 'closed')

        Returns:
            List of cycles
        """
        if status == "active":
            cycles = await self.uow.evaluation_cycles.get_active_cycles()
        elif status:
            cycles = await self.uow.evaluation_cycles.get_by_status(status)
        else:
            cycles = await self.uow.evaluation_cycles.get_all()

        return [EvaluationCycleResponse.model_validate(c) for c in cycles]

    async def update_cycle(
        self, cycle_id: UUID, data: EvaluationCycleUpdate
    ) -> EvaluationCycleResponse:
        """
        Update evaluation cycle.

        Args:
            cycle_id: Cycle UUID
            data: Update data (partial)

        Returns:
            Updated cycle

        Raises:
            NotFoundError: If cycle not found
            ValidationError: If validation fails
        """
        # Get existing cycle
        cycle = await self.uow.evaluation_cycles.get_by_id(cycle_id)
        if not cycle:
            raise NotFoundError(
                message="Evaluation cycle not found",
                details={"cycle_id": str(cycle_id)},
            )

        # Update fields
        update_dict = data.model_dump(exclude_unset=True)

        # Validate dates if both are present
        start_date = update_dict.get("start_date", cycle.start_date)
        end_date = update_dict.get("end_date", cycle.end_date)
        if end_date < start_date:
            raise ValidationError(
                message="End date must be after start date",
                details={"start_date": str(start_date), "end_date": str(end_date)},
            )

        # Validate status
        if "status" in update_dict:
            valid_statuses = {"draft", "active", "closed"}
            if update_dict["status"] not in valid_statuses:
                raise ValidationError(
                    message=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                    details={
                        "status": update_dict["status"],
                        "valid_statuses": list(valid_statuses),
                    },
                )

        # Apply updates
        for key, value in update_dict.items():
            setattr(cycle, key, value)

        updated_cycle = await self.uow.evaluation_cycles.update(cycle)
        await self.uow.session.commit()

        logger.info(
            f"Updated evaluation cycle: {updated_cycle.name}",
            extra={"cycle_id": str(cycle_id), "updated_fields": list(update_dict.keys())},
        )

        return EvaluationCycleResponse.model_validate(updated_cycle)

    async def delete_cycle(self, cycle_id: UUID) -> None:
        """
        Delete evaluation cycle.

        Args:
            cycle_id: Cycle UUID

        Raises:
            NotFoundError: If cycle not found
            ValidationError: If cycle has associated evaluations
        """
        # Get existing cycle
        cycle = await self.uow.evaluation_cycles.get_by_id(cycle_id)
        if not cycle:
            raise NotFoundError(
                message="Evaluation cycle not found",
                details={"cycle_id": str(cycle_id)},
            )

        # Check for associated evaluations
        evaluations = await self.uow.evaluations.get_by_cycle(cycle_id)
        if evaluations:
            raise ValidationError(
                message="Cannot delete cycle with associated evaluations",
                details={
                    "cycle_id": str(cycle_id),
                    "evaluation_count": len(evaluations),
                },
            )

        await self.uow.evaluation_cycles.delete(cycle_id)
        await self.uow.session.commit()

        logger.info(
            f"Deleted evaluation cycle: {cycle.name}",
            extra={"cycle_id": str(cycle_id)},
        )
