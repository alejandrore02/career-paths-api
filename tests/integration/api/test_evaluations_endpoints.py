"""
Integration tests for Evaluation endpoints.

These tests verify the complete flow from HTTP request to database,
using a real test database but mocking external AI services.

Tests cover the critical evaluation flows from flows.md:
- Flow 1, Step 1: Create evaluation
- Flow 1, Step 2-7: Process evaluation (with AI mocked)
"""

from uuid import uuid4

import pytest

from app.db.models.core.user import User
from app.main import app
from app.db.session import get_db



# ============================================================================
# POST /api/v1/evaluations - Create Evaluation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_evaluation_returns_201(
    async_client,
    sample_user,
    sample_evaluator,
    sample_cycle,
    sample_skills,
):
    """
    POST /evaluations should return 201 with created evaluation.
    
    Implements Flow 1, Step 1 from flows.md:
    - Validates user, evaluator, cycle exist
    - Ensures cycle is active
    - Creates evaluation with status='submitted'
    - Normalizes competencies to skill_ids
    - Creates competency scores
    
    Expected Response Structure:
    {
        "id": "uuid",
        "user_id": "uuid",
        "evaluator_id": "uuid",
        "evaluation_cycle_id": "uuid",
        "evaluator_relationship": "manager",
        "status": "submitted",
        "created_at": "timestamp",
        ...
    }
    """
    # Arrange: Prepare request payload
    payload = {
        "user_id": str(sample_user.id),
        "evaluator_id": str(sample_evaluator.id),
        "evaluation_cycle_id": str(sample_cycle.id),
        "evaluator_relationship": "manager",
        "competencies": [
            {
                "competency_name": "Liderazgo",
                "score": 8.5,
                "comments": "Demuestra gran capacidad para coordinar equipos",
            },
            {
                "competency_name": "Comunicación",
                "score": 8.0,
                "comments": "Excelente comunicación escrita y verbal",
            },
        ],
    }

    # Act: POST request to create evaluation
    response = await async_client.post("/api/v1/evaluations", json=payload)
    
    # Assert: Response status and structure
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "id" in data, "Response should include evaluation id"
    assert data["user_id"] == str(sample_user.id), "user_id should match request"
    assert data["evaluator_id"] == str(sample_evaluator.id), "evaluator_id should match request"
    assert data["evaluation_cycle_id"] == str(sample_cycle.id), "cycle_id should match request"
    assert data["evaluator_relationship"] == "manager", "relationship should match request"
    assert data["status"] == "submitted", "Status should be 'submitted'"
    assert "created_at" in data, "Response should include created_at timestamp"
    
    # Verify competencies were created
    # Note: Depending on schema, competencies might be nested or separate endpoint
    # This assumes they're included in the response
    if "competencies" in data or "competency_scores" in data:
        scores_key = "competencies" if "competencies" in data else "competency_scores"
        assert len(data[scores_key]) == 2, "Should have 2 competency scores"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_evaluation_validates_user_exists(
    async_client,
    sample_evaluator,
    sample_cycle,
):
    """
    Should return 404 when user_id does not exist.
    
    Validation order: user → evaluator → cycle → skills
    """
    # Arrange: Payload with non-existent user
    nonexistent_user_id = uuid4()
    
    payload = {
        "user_id": str(nonexistent_user_id),
        "evaluator_id": str(sample_evaluator.id),
        "evaluation_cycle_id": str(sample_cycle.id),
        "evaluator_relationship": "manager",
        "competencies": [
            {
                "competency_name": "Liderazgo",
                "score": 8.0,
            }
        ],
    }
    
    # Act: POST request
    response = await async_client.post("/api/v1/evaluations", json=payload)
    
    # Assert: 404 Not Found
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    error_data = response.json()
    assert "error" in error_data or "detail" in error_data, "Should have error message"
    error_msg = str(error_data).lower()
    assert "user" in error_msg or "not found" in error_msg, "Error should mention user not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_evaluation_validates_cycle_active(
    async_client,
    sample_user,
    sample_evaluator,
    inactive_cycle,
):
    """
    Should return 422 when cycle is not active.
    
    Business rule: Only active cycles accept new evaluations.
    """
    # Arrange: Payload with inactive cycle
    payload = {
        "user_id": str(sample_user.id),
        "evaluator_id": str(sample_evaluator.id),
        "evaluation_cycle_id": str(inactive_cycle.id),
        "evaluator_relationship": "manager",
        "competencies": [
            {
                "competency_name": "Liderazgo",
                "score": 8.0,
            }
        ],
    }
    
    # Act: POST request
    response = await async_client.post("/api/v1/evaluations", json=payload)
    
    # Assert: 422 Validation Error
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    error_data = response.json()
    error_msg = str(error_data).lower()
    assert "active" in error_msg or "closed" in error_msg, "Error should mention cycle status"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_evaluation_validates_competency_exists(
    async_client,
    sample_user,
    sample_evaluator,
    sample_cycle,
):
    """
    Should return 422 when competency name does not exist in skills catalog.
    
    All competencies must be normalized to existing skills.
    """
    # Arrange: Payload with non-existent competency
    payload = {
        "user_id": str(sample_user.id),
        "evaluator_id": str(sample_evaluator.id),
        "evaluation_cycle_id": str(sample_cycle.id),
        "evaluator_relationship": "manager",
        "competencies": [
            {
                "competency_name": "NonexistentCompetency12345",
                "score": 8.0,
            }
        ],
    }
    
    # Act: POST request
    response = await async_client.post("/api/v1/evaluations", json=payload)
    
    # Assert: 422 Validation Error
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    error_data = response.json()
    error_msg = str(error_data).lower()
    assert "skill" in error_msg or "competency" in error_msg, "Error should mention skill/competency"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_evaluation_validates_score_range(
    async_client,
    sample_user,
    sample_evaluator,
    sample_cycle,
):
    """
    Should return 422 when competency score is outside valid range (0-10).
    
    Pydantic schema validation should catch this.
    """
    # Arrange: Payload with invalid score
    payload = {
        "user_id": str(sample_user.id),
        "evaluator_id": str(sample_evaluator.id),
        "evaluation_cycle_id": str(sample_cycle.id),
        "evaluator_relationship": "manager",
        "competencies": [
            {
                "competency_name": "Liderazgo",
                "score": 15.0,  # Invalid: > 10
            }
        ],
    }
    
    # Act: POST request
    response = await async_client.post("/api/v1/evaluations", json=payload)
    
    # Assert: 422 Validation Error
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"


# ============================================================================
# POST /api/v1/evaluations/{id}/process - Process Evaluation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_evaluation_with_complete_cycle(
    async_client,
    sample_user,
    sample_manager,
    sample_cycle,
    sample_skills,
    db_session,
    mocker,
):
    """
    POST /evaluations/{id}/process should process when cycle complete.
    
    Implements Flow 1, Steps 2-7 from flows.md:
    - Detects cycle completion
    - Aggregates scores
    - Calls AI Skills service (mocked)
    - Creates skills assessment
    - Returns processing result
    
    This test requires creating all necessary evaluations first.
    """
    # Arrange: Create complete set of evaluations
    from app.db.models import Evaluation, EvaluationCompetencyScore
    
    skill_liderazgo = next(s for s in sample_skills if s.name == "Liderazgo")
    
    # Self evaluation
    peer1_user = User(
        id=uuid4(),
        email="peer1@example.com",
        full_name="Peer 1",
        is_active=True,
    )
    peer2_user = User(
        id=uuid4(),
        email="peer2@example.com",
        full_name="Peer 2",
        is_active=True,
    )
    db_session.add_all([peer1_user, peer2_user])
    await db_session.flush()

    # Self evaluation
    self_eval = Evaluation(
        id=uuid4(),
        user_id=sample_user.id,
        evaluator_id=sample_user.id,
        evaluation_cycle_id=sample_cycle.id,
        evaluator_relationship="self",
        status="submitted",
    )
    db_session.add(self_eval)
    await db_session.flush()

    self_score = EvaluationCompetencyScore(
        id=uuid4(),
        evaluation_id=self_eval.id,
        skill_id=skill_liderazgo.id,
        score=9.0,
        comments="Me considero líder efectivo",
    )
    db_session.add(self_score)

    # Manager evaluation
    manager_eval = Evaluation(
        id=uuid4(),
        user_id=sample_user.id,
        evaluator_id=sample_manager.id,
        evaluation_cycle_id=sample_cycle.id,
        evaluator_relationship="manager",
        status="submitted",
    )
    db_session.add(manager_eval)
    await db_session.flush()

    manager_score = EvaluationCompetencyScore(
        id=uuid4(),
        evaluation_id=manager_eval.id,
        skill_id=skill_liderazgo.id,
        score=8.0,
        comments="Buen liderazgo de equipo",
    )
    db_session.add(manager_score)

    # Peer evaluations (2 required)
    peer1 = Evaluation(
        id=uuid4(),
        user_id=sample_user.id,
        evaluator_id=peer1_user.id,
        evaluation_cycle_id=sample_cycle.id,
        evaluator_relationship="peer",
        status="submitted",
    )
    db_session.add(peer1)
    await db_session.flush()

    peer1_score = EvaluationCompetencyScore(
        id=uuid4(),
        evaluation_id=peer1.id,
        skill_id=skill_liderazgo.id,
        score=7.5,
    )
    db_session.add(peer1_score)

    peer2 = Evaluation(
        id=uuid4(),
        user_id=sample_user.id,
        evaluator_id=peer2_user.id,
        evaluation_cycle_id=sample_cycle.id,
        evaluator_relationship="peer",
        status="submitted",
    )
    db_session.add(peer2)
    await db_session.flush()

    peer2_score = EvaluationCompetencyScore(
        id=uuid4(),
        evaluation_id=peer2.id,
        skill_id=skill_liderazgo.id,
        score=8.0,
    )
    db_session.add(peer2_score)

    await db_session.commit()

    # Mock AI Skills client
    mock_ai_response = {
        "assessment_id": str(uuid4()),
        "skills_profile": {
            "strengths": [
                {
                    "skill": "Liderazgo",
                    "score": 8.1,
                    "evidence": "Consistentemente evaluado alto",
                }
            ],
            "growth_areas": [],
            "hidden_talents": [],
            "role_readiness": [],
        },
    }

    mocker.patch(
        "app.integrations.ai_skills_client.AISkillsClient.assess_skills",
        return_value=mock_ai_response,
    )

    response = await async_client.post(f"/api/v1/evaluations/{self_eval.id}/process")

    assert response.status_code in [200, 202], f"Expected 200/202, got {response.status_code}: {response.text}"

    data = response.json()
    assert "evaluation_id" in data
    assert "cycle_complete" in data
    assert data["cycle_complete"] is True
    assert data["message"] == "Evaluation processed. Ready for Skills Assessment."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_evaluation_with_incomplete_cycle(
    async_client,
    sample_user,
    sample_cycle,
    sample_skills,
    db_session,
):
    """
    POST /evaluations/{id}/process should return 409 when cycle incomplete.
    
    Missing required evaluations should result in Conflict error.
    """
    # Arrange: Create incomplete evaluations (missing manager)
    from app.db.models import Evaluation, EvaluationCompetencyScore
    
    skill = sample_skills[0]
    
    # Only self evaluation (missing manager and peers)
    self_eval = Evaluation(
        id=uuid4(),
        user_id=sample_user.id,
        evaluator_id=sample_user.id,
        evaluation_cycle_id=sample_cycle.id,
        evaluator_relationship="self",
        status="submitted",
    )
    db_session.add(self_eval)
    await db_session.flush()
    
    score = EvaluationCompetencyScore(
        id=uuid4(),
        evaluation_id=self_eval.id,
        skill_id=skill.id,
        score=8.0,
    )
    db_session.add(score)
    await db_session.commit()
    
    # Act: Try to process
    response = await async_client.post(f"/api/v1/evaluations/{self_eval.id}/process")
    
    # Assert: 409 Conflict
    assert response.status_code == 409, f"Expected 409, got {response.status_code}"
    
    error_data = response.json()
    error_msg = str(error_data).lower()
    assert "incomplete" in error_msg or "missing" in error_msg, "Error should indicate cycle incomplete"


# ============================================================================
# GET /api/v1/evaluations/{id} - Get Evaluation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_evaluation_returns_200(
    async_client,
    sample_user,
    sample_evaluator,
    sample_cycle,
    sample_skills,
    db_session,
):
    """
    GET /evaluations/{id} should return evaluation with competency scores.
    
    Response should include full evaluation details and related entities.
    """
    # Arrange: Create evaluation in database
    from app.db.models import Evaluation, EvaluationCompetencyScore
    
    skill = sample_skills[0]
    
    evaluation = Evaluation(
        id=uuid4(),
        user_id=sample_user.id,
        evaluator_id=sample_evaluator.id,
        evaluation_cycle_id=sample_cycle.id,
        evaluator_relationship="peer",
        status="submitted",
    )
    db_session.add(evaluation)
    await db_session.flush()
    
    score = EvaluationCompetencyScore(
        id=uuid4(),
        evaluation_id=evaluation.id,
        skill_id=skill.id,
        score=7.5,
        comments="Good performance",
    )
    db_session.add(score)
    await db_session.commit()
    
    # Act: GET request
    response = await async_client.get(f"/api/v1/evaluations/{evaluation.id}")
    
    # Assert: 200 OK with evaluation data
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["id"] == str(evaluation.id), "Should return correct evaluation"
    assert data["user_id"] == str(sample_user.id), "Should include user_id"
    assert data["status"] == "submitted", "Should include status"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_evaluation_not_found_returns_404(async_client):
    """
    GET /evaluations/{id} should return 404 for non-existent evaluation.
    """
    # Arrange: Non-existent evaluation ID
    nonexistent_id = uuid4()
    
    # Act: GET request
    response = await async_client.get(f"/api/v1/evaluations/{nonexistent_id}")
    
    # Assert: 404 Not Found
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
