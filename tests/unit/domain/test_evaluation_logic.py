"""Tests for domain layer - evaluation business logic."""

from uuid import uuid4
from typing import Iterable

import pytest

from app.domain.evaluation_logic import (
    is_cycle_complete_for_user,
    aggregate_competency_scores,
)
from app.domain.entities.evaluation import EvaluationEntity, CompetencyScore

# ============================================================================
# Test helpers / factories (pure, no DB)
# ============================================================================

def make_evaluation(
    *,
    user_id,
    cycle_id,
    relationship: str,
    status: str = "submitted",
    evaluator_id=None,
) -> EvaluationEntity:
    """
    Factory for EvaluationEntity objects used in domain tests.

    Pure domain objects - no database involved.
    """
    return EvaluationEntity(
        id=uuid4(),
        user_id=user_id,
        evaluation_cycle_id=cycle_id,
        evaluator_id=evaluator_id or uuid4(),
        evaluator_relationship=relationship,
        status=status,
        competency_scores=[],  # Empty by default
    )


def make_eval_with_score(
    *,
    user_id,
    cycle_id,
    relationship: str,
    skill_id,
    score: float,
    status: str = "submitted",
    comments: str | None = None,
) -> EvaluationEntity:
    """
    Factory para crear una EvaluationEntity con un único CompetencyScore.
    """
    evaluation = make_evaluation(
        user_id=user_id,
        cycle_id=cycle_id,
        relationship=relationship,
        status=status,
    )
    # Replace empty list with actual score
    return EvaluationEntity(
        id=evaluation.id,
        user_id=evaluation.user_id,
        evaluation_cycle_id=evaluation.evaluation_cycle_id,
        evaluator_id=evaluation.evaluator_id,
        evaluator_relationship=evaluation.evaluator_relationship,
        status=evaluation.status,
        competency_scores=[
            CompetencyScore(
                skill_id=skill_id,
                score=score,
                comments=comments,
            )
        ],
    )


def make_many_peer_evals_with_score(
    *,
    n: int,
    user_id,
    cycle_id,
    skill_id,
    score: float,
    status: str = "submitted",
) -> list[EvaluationEntity]:
    """
    Crea n evaluaciones 'peer' con el mismo score.
    """
    return [
        make_eval_with_score(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
            skill_id=skill_id,
            score=score,
            status=status,
        )
        for _ in range(n)
    ]


# ============================================================================
# Tests for is_cycle_complete_for_user
# ============================================================================

@pytest.mark.unit
def test_is_cycle_complete_all_requirements_met():
    """
    Should return (True, None) when all evaluation requirements are met.
    
    Business rule: Cycle is complete when user has:
    - At least 1 self-evaluation
    - At least 1 manager evaluation
    - At least 2 peer evaluations
    - At least 0 direct_report evaluations (default)
    """
    user_id = uuid4()
    cycle_id = uuid4()

    evaluations = [
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="self",
            evaluator_id=user_id,
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="manager",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
        ),
    ]
    
    is_complete, reason = is_cycle_complete_for_user(evaluations)
    
    assert is_complete is True, "Cycle should be complete when all requirements are met"
    assert reason is None, "Reason should be None when cycle is complete"


@pytest.mark.unit
def test_is_cycle_complete_missing_self_evaluation():
    """
    Should return (False, reason) when self-evaluation is missing.
    """
    user_id = uuid4()
    cycle_id = uuid4()
    
    evaluations = [
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="manager",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
        ),
    ]
    
    is_complete, reason = is_cycle_complete_for_user(evaluations)
    
    assert is_complete is False, "Cycle should be incomplete without self-evaluation"
    assert reason is not None
    assert "self-evaluation" in reason.lower()


@pytest.mark.unit
def test_is_cycle_complete_missing_manager_evaluation():
    """
    Should return (False, reason) when manager evaluation is missing.
    """
    user_id = uuid4()
    cycle_id = uuid4()
    
    evaluations = [
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="self",
            evaluator_id=user_id,
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
        ),
    ]
    
    is_complete, reason = is_cycle_complete_for_user(evaluations)
    
    assert is_complete is False, "Cycle should be incomplete without manager evaluation"
    assert reason is not None
    assert "manager" in reason.lower()


@pytest.mark.unit
def test_is_cycle_complete_insufficient_peer_evaluations():
    """
    Should return (False, reason) when fewer than 2 peer evaluations exist.
    """
    user_id = uuid4()
    cycle_id = uuid4()
    
    evaluations = [
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="self",
            evaluator_id=user_id,
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="manager",
        ),
        # Only 1 peer
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
        ),
    ]
    
    is_complete, reason = is_cycle_complete_for_user(evaluations)
    
    assert is_complete is False
    assert reason is not None
    assert "peer" in reason.lower()
    assert "2" in reason or "has 1" in reason


@pytest.mark.unit
def test_is_cycle_complete_ignores_non_submitted():
    """
    Should only count evaluations with status='submitted'.
    """
    user_id = uuid4()
    cycle_id = uuid4()
    
    evaluations = [
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="self",
            evaluator_id=user_id,
            status="submitted",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="manager",
            status="submitted",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
            status="submitted",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
            status="pending",
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
            status="cancelled",
        ),
    ]
    
    is_complete, reason = is_cycle_complete_for_user(evaluations)
    
    assert is_complete is False, "Should only count submitted evaluations"
    assert "peer" in (reason or "").lower()


@pytest.mark.unit
def test_is_cycle_complete_with_custom_minimums():
    """
    Should respect custom minimum requirements for peers and direct reports.
    """
    user_id = uuid4()
    cycle_id = uuid4()
    
    evaluations = [
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="self",
            evaluator_id=user_id,
        ),
        make_evaluation(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="manager",
        ),
        # 3 peers
        *[
            make_evaluation(
                user_id=user_id,
                cycle_id=cycle_id,
                relationship="peer",
            )
            for _ in range(3)
        ],
        # 2 direct reports
        *[
            make_evaluation(
                user_id=user_id,
                cycle_id=cycle_id,
                relationship="direct_report",
            )
            for _ in range(2)
        ],
    ]
    
    is_complete, reason = is_cycle_complete_for_user(
        evaluations,
        min_peers=3,
        min_direct_reports=2,
    )
    
    assert is_complete is True
    assert reason is None


# ============================================================================
# Tests for aggregate_competency_scores
# ============================================================================

@pytest.mark.unit
def test_aggregate_scores_calculates_overall_average():
    """
    Should calculate correct overall average score across all evaluations.
    """
    skill_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()
    
    expected_scores = [8.0, 7.0, 9.0, 6.0]  # avg = 7.5
    
    evaluations = [
        make_eval_with_score(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
            skill_id=skill_id,
            score=score,
            comments=f"Test comment {i}",
        )
        for i, score in enumerate(expected_scores)
    ]
    
    result = aggregate_competency_scores(evaluations)
    
    assert skill_id in result
    assert result[skill_id]["overall_avg"] == 7.5


@pytest.mark.unit
def test_aggregate_scores_calculates_per_relationship():
    """
    Should calculate separate averages for each evaluator relationship.
    """
    skill_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()
    
    self_eval = make_eval_with_score(
        user_id=user_id,
        cycle_id=cycle_id,
        relationship="self",
        skill_id=skill_id,
        score=9.0,
    )
    manager_eval = make_eval_with_score(
        user_id=user_id,
        cycle_id=cycle_id,
        relationship="manager",
        skill_id=skill_id,
        score=7.0,
    )
    peer_evals = [
        make_eval_with_score(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="peer",
            skill_id=skill_id,
            score=score,
        )
        for score in (8.0, 6.0)
    ]
    
    evaluations = [self_eval, manager_eval, *peer_evals]
    
    result = aggregate_competency_scores(evaluations)
    stats = result[skill_id]
    
    assert stats["self_avg"] == 9.0
    assert stats["manager_avg"] == 7.0
    assert stats["peer_avg"] == 7.0


@pytest.mark.unit
@pytest.mark.parametrize(
    "n, expected_confidence",
    [
        (5, 0.9),  # n >= 5
        (3, 0.7),  # n >= 3
        (1, 0.5),  # n >= 1
    ],
)
def test_aggregate_scores_confidence_by_sample_size(n, expected_confidence):
    """
    Should calculate confidence score based on sample size.

    Confidence increases with more evaluations:
    - n >= 5: confidence = 0.9
    - n >= 3: confidence = 0.7
    - n >= 1: confidence = 0.5
    """
    skill_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()
    
    evaluations = make_many_peer_evals_with_score(
        n=n,
        user_id=user_id,
        cycle_id=cycle_id,
        skill_id=skill_id,
        score=7.0,
    )
    
    result = aggregate_competency_scores(evaluations)
    
    assert result[skill_id]["confidence"] == expected_confidence


@pytest.mark.unit
def test_aggregate_scores_includes_raw_stats():
    """
    Should include raw statistics with counts per relationship.
    """
    skill_id = uuid4()
    user_id = uuid4()
    cycle_id = uuid4()
    
    evaluations: list[EvaluationEntity] = []

    evaluations.append(
        make_eval_with_score(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="self",
            skill_id=skill_id,
            score=8.0,
        )
    )
    evaluations.append(
        make_eval_with_score(
            user_id=user_id,
            cycle_id=cycle_id,
            relationship="manager",
            skill_id=skill_id,
            score=7.0,
        )
    )
    evaluations.extend(
        make_many_peer_evals_with_score(
            n=3,
            user_id=user_id,
            cycle_id=cycle_id,
            skill_id=skill_id,
            score=7.5,
        )
    )
    
    result = aggregate_competency_scores(evaluations)
    raw_stats = result[skill_id].get("raw_stats", {})
    
    assert raw_stats.get("n_self") == 1
    assert raw_stats.get("n_manager") == 1
    assert raw_stats.get("n_peer") == 3
    assert raw_stats.get("n_direct_report") == 0
    assert raw_stats.get("self_avg") == 8.0
    assert raw_stats.get("manager_avg") == 7.0
    assert raw_stats.get("peer_avg") == 7.5
