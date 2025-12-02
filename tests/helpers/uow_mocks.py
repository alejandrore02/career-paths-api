# tests/helpers/uow_mocks.py
from __future__ import annotations

from typing import Iterable
from unittest.mock import AsyncMock, MagicMock


class UowMockBuilder:
    """
    Small builder to create a UnitOfWork mock with common methods preconfigured.

    Uso típico:
        builder = UowMockBuilder()
        mock_uow = (
            builder
            .with_users(mock_user, mock_evaluator)
            .with_cycle(mock_cycle)
            .with_skill(mock_skill)
            .build()
        )
    """

    def __init__(self) -> None:
        self.uow = MagicMock()

        # repos comunes
        self.uow.users.get_by_id = AsyncMock()
        self.uow.evaluation_cycles.get_by_id = AsyncMock()
        self.uow.skills.get_by_name = AsyncMock()
        self.uow.skills.get_by_names = AsyncMock()
        self.uow.skills.get_by_id = AsyncMock()
        self.uow.skills.get_by_ids = AsyncMock()
        self.uow.evaluations.get_by_id = AsyncMock()
        self.uow.evaluations.get_by_user_and_cycle = AsyncMock()
        self.uow.competency_scores.create_bulk = AsyncMock()
        self.uow.user_skill_scores.delete_by_user_and_cycle = AsyncMock()
        self.uow.user_skill_scores.create_bulk = AsyncMock()

        # commit / session
        self.uow.commit = AsyncMock()
        self.uow.session = MagicMock()

    # --------- Configuración fluida ---------

    def with_users(self, *users) -> UowMockBuilder:
        """
        Configura users.get_by_id para devolver los usuarios
        en orden de llamada (user, evaluator, etc.).
        """
        self.uow.users.get_by_id = AsyncMock(side_effect=list(users))
        return self

    def with_cycle(self, cycle) -> UowMockBuilder:
        self.uow.evaluation_cycles.get_by_id = AsyncMock(return_value=cycle)
        return self

    def with_skill(self, skill) -> UowMockBuilder:
        self.uow.skills.get_by_name = AsyncMock(return_value=skill)
        return self

    def with_skills(self, *skills) -> UowMockBuilder:
        """Configure skills.get_by_names to return the provided skills."""
        self.uow.skills.get_by_names = AsyncMock(return_value=list(skills))
        # Also setup get_by_ids for batching by UUID
        self.uow.skills.get_by_ids = AsyncMock(return_value=list(skills))
        return self

    def with_evaluation(self, evaluation) -> UowMockBuilder:
        self.uow.evaluations.get_by_id = AsyncMock(return_value=evaluation)
        return self

    def with_evaluations_for_user_cycle(
        self,
        evaluations: Iterable,
    ) -> UowMockBuilder:
        self.uow.evaluations.get_by_user_and_cycle = AsyncMock(
            return_value=list(evaluations)
        )
        return self

    def with_delete_skill_scores_result(
        self,
        deleted_count: int = 0,
    ) -> UowMockBuilder:
        self.uow.user_skill_scores.delete_by_user_and_cycle = AsyncMock(
            return_value=deleted_count
        )
        return self

    def build(self) -> MagicMock:
        """Return the configured mock UnitOfWork."""
        return self.uow
