# tests/factories/evaluations.py
from uuid import uuid4
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Evaluation,
    EvaluationCompetencyScore,
    User,
    Skill,
    EvaluationCycle,
)


async def create_evaluation_with_scores(
    db_session: AsyncSession,
    *,
    user: User,
    evaluator: User,
    cycle: EvaluationCycle,
    relationship: str,
    scores: Iterable[tuple[Skill, float]],
    status: str = "submitted",
    comments: str | None = None,
) -> Evaluation:
    """
    Create an Evaluation and its EvaluationCompetencyScore rows.
    """
    evaluation = Evaluation(
        id=uuid4(),
        user_id=user.id,
        evaluator_id=evaluator.id,
        evaluation_cycle_id=cycle.id,
        evaluator_relationship=relationship,
        status=status,
    )
    db_session.add(evaluation)
    await db_session.flush()

    for skill, score in scores:
        comp_score = EvaluationCompetencyScore(
            id=uuid4(),
            evaluation_id=evaluation.id,
            skill_id=skill.id,
            score=score,
            comments=comments,
        )
        db_session.add(comp_score)

    await db_session.flush()
    await db_session.refresh(evaluation)
    return evaluation


async def create_full_360_cycle_for_user(
    db_session: AsyncSession,
    *,
    user: User,
    manager: User,
    peers: list[User],
    cycle: EvaluationCycle,
    skill: Skill,
) -> dict:
    """
    Create a complete 360° set of evaluations for a given user:
    - 1 self
    - 1 manager
    - ≥2 peers
    """
    # self
    self_eval = await create_evaluation_with_scores(
        db_session,
        user=user,
        evaluator=user,
        cycle=cycle,
        relationship="self",
        scores=[(skill, 9.0)],
        comments="Self-evaluation",
    )

    # manager
    manager_eval = await create_evaluation_with_scores(
        db_session,
        user=user,
        evaluator=manager,
        cycle=cycle,
        relationship="manager",
        scores=[(skill, 8.0)],
        comments="Manager evaluation",
    )

    peer_evals: list[Evaluation] = []
    for i, peer in enumerate(peers, start=1):
        peer_eval = await create_evaluation_with_scores(
            db_session,
            user=user,
            evaluator=peer,
            cycle=cycle,
            relationship="peer",
            scores=[(skill, 7.5 + 0.5 * (i % 2))],
            comments=f"Peer {i} evaluation",
        )
        peer_evals.append(peer_eval)

    return {
        "self": self_eval,
        "manager": manager_eval,
        "peers": peer_evals,
    }
