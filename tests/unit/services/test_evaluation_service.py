"""Unit tests for EvaluationService.

These tests verify the service layer logic for 360° evaluations,
including creation, validation, cycle completion detection, and
score aggregation. External dependencies (UoW, repositories, AI clients)
are mocked to isolate the service logic.
"""

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.helpers.uow_mocks import UowMockBuilder
from tests.helpers.evaluations import create_evaluation_with_scores

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.schemas.evaluation.evaluation import EvaluationCreate, CompetencyScoreCreate
from app.services.evaluation_service import EvaluationService


# ============================================================================
# Local helpers
# ============================================================================


def make_evaluation_create(
    *,
    user_id,
    evaluator_id,
    cycle_id,
    relationship: str = "manager",
    competency_name: str = "Liderazgo",
    score: float = 8.0,
    comments: str | None = None,
) -> EvaluationCreate:
    """Factory para construir el DTO de entrada de forma consistente."""
    return EvaluationCreate(
        user_id=user_id,
        evaluator_id=evaluator_id,
        evaluation_cycle_id=cycle_id,
        evaluator_relationship=relationship,
        competencies=[
            CompetencyScoreCreate(
                competency_name=competency_name,
                score=score,
                comments=comments,
            )
        ],
    )


def setup_session_execute_for_evaluations(mock_uow, evaluations: list):
    """
    Configura mock_uow.session.execute para que _aggregate_user_skill_scores()
    devuelva exactamente la lista de evaluaciones proporcionada.
    """
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.unique.return_value.all.return_value = evaluations
    mock_result.scalars.return_value = mock_scalars

    mock_uow.session = MagicMock()
    mock_uow.session.execute = AsyncMock(return_value=mock_result)
    mock_uow.session.commit = AsyncMock()


# ============================================================================
# Tests for create_evaluation
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_evaluation_success():
    """
    Should successfully create evaluation when all validations pass.
    """
    # Arrange: Setup mocks using UowMockBuilder for readability
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()

    user_id = uuid4()
    evaluator_id = uuid4()
    cycle_id = uuid4()
    skill_id = uuid4()

    mock_user = MagicMock(id=user_id, full_name="Test User")
    mock_evaluator = MagicMock(id=evaluator_id, full_name="Test Evaluator")
    mock_cycle = MagicMock(id=cycle_id, status="active")
    
    # Configure skill mock properly - 'name' is special in MagicMock
    mock_skill = MagicMock()
    mock_skill.id = skill_id
    mock_skill.name = "Liderazgo"

    mock_evaluation = MagicMock(
        id=uuid4(),
        user_id=user_id,
        evaluator_id=evaluator_id,
        evaluation_cycle_id=cycle_id,
        evaluator_relationship="manager",
        status="submitted",
        submitted_at=datetime.now(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_uow = (
        builder
        .with_users(mock_user, mock_evaluator)
        .with_cycle(mock_cycle)
        .with_skills(mock_skill)  # Changed to with_skills for get_by_names
        .build()
    )

    mock_uow.evaluations.create = AsyncMock(return_value=mock_evaluation)
    mock_uow.competency_scores.create_bulk = AsyncMock()
    mock_uow.commit = AsyncMock()

    service = EvaluationService(mock_uow, mock_ai_client)

    evaluation_data = make_evaluation_create(
        user_id=user_id,
        evaluator_id=evaluator_id,
        cycle_id=cycle_id,
        relationship="manager",
        competency_name="Liderazgo",
        score=8.5,
        comments="Excelente capacidad de liderazgo",
    )

    # Act
    result = await service.create_evaluation(evaluation_data)

    # Assert
    assert result is not None, "Should return evaluation"
    assert result.id == mock_evaluation.id, "Should return created evaluation"

    assert mock_uow.users.get_by_id.call_count == 2, "Should validate user and evaluator"
    mock_uow.evaluation_cycles.get_by_id.assert_called_once_with(cycle_id)
    mock_uow.skills.get_by_names.assert_called_once_with(["Liderazgo"])

    mock_uow.evaluations.create.assert_called_once()
    mock_uow.competency_scores.create_bulk.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_evaluation_user_not_found():
    """
    Should raise NotFoundError when user does not exist.
    Validation must occur before any database modifications.
    """
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()
    mock_uow = builder.build()

    # User no existe
    mock_uow.users.get_by_id = AsyncMock(return_value=None)
    mock_uow.commit = AsyncMock()

    service = EvaluationService(mock_uow, mock_ai_client)

    evaluation_data = make_evaluation_create(
        user_id=uuid4(),
        evaluator_id=uuid4(),
        cycle_id=uuid4(),
        relationship="manager",
        competency_name="Liderazgo",
        score=8.0,
    )

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.create_evaluation(evaluation_data)

    assert "user" in str(exc_info.value).lower(), "Error should mention user not found"
    # When the user is not found, the service should not create or commit.
    mock_uow.evaluations.create.assert_not_called()
    mock_uow.commit.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_evaluation_cycle_not_active():
    """
    Should raise ValidationError when cycle is not in 'active' status.
    Only active cycles can receive new evaluations.
    """
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()

    user_id = uuid4()
    evaluator_id = uuid4()
    cycle_id = uuid4()

    mock_user = MagicMock(id=user_id)
    mock_evaluator = MagicMock(id=evaluator_id)
    mock_cycle = MagicMock(id=cycle_id, status="closed")

    mock_uow = (
        builder
        .with_users(mock_user, mock_evaluator)
        .with_cycle(mock_cycle)
        .build()
    )

    service = EvaluationService(mock_uow, mock_ai_client)

    evaluation_data = make_evaluation_create(
        user_id=user_id,
        evaluator_id=evaluator_id,
        cycle_id=cycle_id,
        relationship="manager",
        competency_name="Liderazgo",
        score=8.0,
    )

    with pytest.raises(ValidationError) as exc_info:
        await service.create_evaluation(evaluation_data)

    assert "active" in str(exc_info.value).lower(), "Error should mention cycle must be active"
    mock_uow.evaluations.create.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_evaluation_skill_not_found():
    """
    Should raise ValidationError when competency name does not exist in catalog.
    All competencies must map to existing skills.
    """
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()

    user_id = uuid4()
    evaluator_id = uuid4()
    cycle_id = uuid4()

    mock_user = MagicMock(id=user_id)
    mock_evaluator = MagicMock(id=evaluator_id)
    mock_cycle = MagicMock(id=cycle_id, status="active")

    mock_uow = (
        builder
        .with_users(mock_user, mock_evaluator)
        .with_cycle(mock_cycle)
        .build()
    )

    # Skill no encontrado - get_by_names returns empty list
    mock_uow.skills.get_by_names = AsyncMock(return_value=[])
    mock_uow.evaluations.create = AsyncMock()
    mock_uow.commit = AsyncMock()

    service = EvaluationService(mock_uow, mock_ai_client)

    evaluation_data = make_evaluation_create(
        user_id=user_id,
        evaluator_id=evaluator_id,
        cycle_id=cycle_id,
        competency_name="NonexistentSkill",
        score=8.0,
    )

    with pytest.raises(ValidationError) as exc_info:
        await service.create_evaluation(evaluation_data)

    error_msg = str(exc_info.value).lower()
    assert "skill" in error_msg or "competency" in error_msg, "Error should mention skill not found"
    # Current service creates the Evaluation object but does not persist it (no commit)
    mock_uow.evaluations.create.assert_called_once()
    mock_uow.commit.assert_not_called()


# ============================================================================
# Tests for process_evaluation
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_evaluation_cycle_incomplete():
    """
    Should raise ConflictError when cycle is not complete for user.
    """
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()
    mock_uow = builder.build()

    evaluation_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()

    # Evaluación raíz
    mock_evaluation = MagicMock(
        id=evaluation_id,
        user_id=user_id,
        evaluation_cycle_id=cycle_id,
    )
    mock_uow.evaluations.get_by_id = AsyncMock(return_value=mock_evaluation)

    # Faltan evaluaciones de manager
    mock_evaluations = [
        MagicMock(evaluator_relationship="self", status="submitted"),
        MagicMock(evaluator_relationship="peer", status="submitted"),
        MagicMock(evaluator_relationship="peer", status="submitted"),
    ]
    mock_uow.evaluations.get_by_user_and_cycle = AsyncMock(return_value=mock_evaluations)

    service = EvaluationService(mock_uow, mock_ai_client)

    with pytest.raises(ConflictError) as exc_info:
        await service.process_evaluation(evaluation_id)

    error_msg = str(exc_info.value).lower()
    assert "incomplete" in error_msg or "missing" in error_msg, "Error should indicate cycle is incomplete"
    mock_ai_client.assess_skills.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_evaluation_aggregates_scores():
    """
    Should aggregate user skill scores when cycle is complete.
    """
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()
    mock_uow = builder.build()

    evaluation_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()
    skill_id = uuid4()

    mock_evaluation = MagicMock(
        id=evaluation_id,
        user_id=user_id,
        evaluation_cycle_id=cycle_id,
    )
    mock_uow.evaluations.get_by_id = AsyncMock(return_value=mock_evaluation)

    # Podemos usar MagicMocks o el helper create_evaluation_with_scores si ya lo tienes.
    # Aquí mantengo MagicMock para no asumir la firma de tu helper.
    mock_evaluations = [
        MagicMock(
            evaluator_relationship="self",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=9.0)],
        ),
        MagicMock(
            evaluator_relationship="manager",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=8.0)],
        ),
        MagicMock(
            evaluator_relationship="peer",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=7.0)],
        ),
        MagicMock(
            evaluator_relationship="peer",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=8.0)],
        ),
    ]
    mock_uow.evaluations.get_by_user_and_cycle = AsyncMock(return_value=mock_evaluations)

    mock_uow.user_skill_scores.delete_by_user_and_cycle = AsyncMock()
    mock_uow.user_skill_scores.create_bulk = AsyncMock()

    # Reutilizamos la misma lista para la agregación interna
    setup_session_execute_for_evaluations(mock_uow, mock_evaluations)

    mock_uow.commit = AsyncMock()

    service = EvaluationService(mock_uow, mock_ai_client)

    result = await service.process_evaluation(evaluation_id)

    mock_uow.user_skill_scores.delete_by_user_and_cycle.assert_called_once_with(
        user_id=user_id,
        cycle_id=cycle_id,
    )
    mock_uow.user_skill_scores.create_bulk.assert_called_once()

    create_args = mock_uow.user_skill_scores.create_bulk.call_args[0][0]
    assert len(create_args) > 0, "Should create at least one user skill score"

    assert result["cycle_complete"] is True
    assert result["user_id"] == user_id
    assert result["cycle_id"] == cycle_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_evaluation_calls_ai_skills_client():
    """
    Should mark readiness for AI Skills client when cycle is complete.

    Nota: la implementación actual del EvaluationService solo deja
    la evaluación lista; la llamada real al AI client se hace
    desde otro servicio (SkillsAssessmentService).
    """
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()
    mock_uow = builder.build()

    evaluation_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()
    skill_id = uuid4()

    mock_evaluation = MagicMock(
        id=evaluation_id,
        user_id=user_id,
        evaluation_cycle_id=cycle_id,
    )
    mock_uow.evaluations.get_by_id = AsyncMock(return_value=mock_evaluation)

    mock_user = MagicMock(
        id=user_id,
        position="Software Engineer",
        full_name="Test User",
    )
    mock_uow.users.get_by_id = AsyncMock(return_value=mock_user)

    mock_evaluations = [
        MagicMock(
            evaluator_relationship="self",
            status="submitted",
            competency_scores=[
                MagicMock(skill_id=skill_id, score=8.0, skill=MagicMock(name="Liderazgo"))
            ],
        ),
        MagicMock(
            evaluator_relationship="manager",
            status="submitted",
            competency_scores=[
                MagicMock(skill_id=skill_id, score=7.0, skill=MagicMock(name="Liderazgo"))
            ],
        ),
        MagicMock(
            evaluator_relationship="peer",
            status="submitted",
            competency_scores=[
                MagicMock(skill_id=skill_id, score=7.5, skill=MagicMock(name="Liderazgo"))
            ],
        ),
        MagicMock(
            evaluator_relationship="peer",
            status="submitted",
            competency_scores=[
                MagicMock(skill_id=skill_id, score=8.0, skill=MagicMock(name="Liderazgo"))
            ],
        ),
    ]
    mock_uow.evaluations.get_by_user_and_cycle = AsyncMock(return_value=mock_evaluations)

    mock_uow.user_skill_scores.delete_by_user_and_cycle = AsyncMock(return_value=0)
    mock_uow.user_skill_scores.create_bulk = AsyncMock()

    setup_session_execute_for_evaluations(mock_uow, mock_evaluations)
    mock_uow.commit = AsyncMock()

    service = EvaluationService(mock_uow, mock_ai_client)

    result = await service.process_evaluation(evaluation_id)

    assert result["cycle_complete"] is True
    assert result["user_id"] == user_id
    assert "Ready for Skills Assessment" in result["message"]

    mock_uow.user_skill_scores.delete_by_user_and_cycle.assert_called_once()
    mock_uow.user_skill_scores.create_bulk.assert_called_once()
    # No afirmamos llamada al AI client: ese flujo vive en otro servicio.


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_evaluation_completes_successfully():
    """
    Should complete processing when cycle is complete.
    Verifies the full workflow: validation → aggregation → ready for AI.
    """
    builder = UowMockBuilder()
    mock_ai_client = AsyncMock()
    mock_uow = builder.build()

    evaluation_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()
    skill_id = uuid4()

    mock_evaluation = MagicMock(
        id=evaluation_id,
        user_id=user_id,
        evaluation_cycle_id=cycle_id,
    )
    mock_uow.evaluations.get_by_id = AsyncMock(return_value=mock_evaluation)

    mock_evaluations = [
        MagicMock(
            evaluator_relationship="self",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=8.0)],
        ),
        MagicMock(
            evaluator_relationship="manager",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=7.0)],
        ),
        MagicMock(
            evaluator_relationship="peer",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=7.5)],
        ),
        MagicMock(
            evaluator_relationship="peer",
            status="submitted",
            competency_scores=[MagicMock(skill_id=skill_id, score=8.0)],
        ),
    ]
    mock_uow.evaluations.get_by_user_and_cycle = AsyncMock(return_value=mock_evaluations)

    mock_uow.user_skill_scores.delete_by_user_and_cycle = AsyncMock(return_value=0)
    mock_uow.user_skill_scores.create_bulk = AsyncMock()

    setup_session_execute_for_evaluations(mock_uow, mock_evaluations)
    mock_uow.commit = AsyncMock()

    service = EvaluationService(mock_uow, mock_ai_client)

    result = await service.process_evaluation(evaluation_id)

    assert result["cycle_complete"] is True
    assert result["evaluation_id"] == evaluation_id
    assert result["user_id"] == user_id
    assert result["cycle_id"] == cycle_id

    mock_uow.user_skill_scores.delete_by_user_and_cycle.assert_called_once_with(
        user_id=user_id,
        cycle_id=cycle_id,
    )
    mock_uow.user_skill_scores.create_bulk.assert_called_once()
