"""
Domain logic for evaluations.

This module contains business rules for 360° evaluations:
- Cycle completion detection
- Score aggregation logic
- Validation rules

IMPORTANT: This module uses domain entities (pure Python) instead of ORM models.
No dependencies on SQLAlchemy or frameworks.
"""
from typing import Optional, Sequence
from uuid import UUID

# Use domain entities for rich business logic
from app.domain.entities.evaluation import EvaluationEntity


def is_cycle_complete_for_user(
    evaluations: Sequence[EvaluationEntity],
    min_peers: int = 2,
    min_direct_reports: int = 0,
) -> tuple[bool, Optional[str]]:
    """
    Determine if a user has completed all required evaluations for a cycle.
    
    Business rules (as per flows.md):
    - Must have at least 1 self-evaluation
    - Must have at least 1 manager evaluation
    - Must have at least min_peers peer evaluations
    - Must have at least min_direct_reports direct report evaluations (if applicable)
    
    Args:
        evaluations: Sequence of evaluations for a user in a specific cycle
        min_peers: Minimum number of peer evaluations required
        min_direct_reports: Minimum number of direct report evaluations required
        
    Returns:
        Tuple of (is_complete: bool, reason: Optional[str])
        - If complete: (True, None)
        - If incomplete: (False, "description of what's missing")
    """
    # Count evaluations by relationship type
    counts = {
        "self": 0,
        "manager": 0,
        "peer": 0,
        "direct_report": 0,
    }
    
    for evaluation in evaluations:
        # Only count submitted evaluations
        if evaluation.is_submitted():  # Use domain method
            rel = evaluation.evaluator_relationship
            if rel in counts:
                counts[rel] += 1
    
    # Check requirements
    missing_parts = []
    
    if counts["self"] < 1:
        missing_parts.append("self-evaluation")
    
    if counts["manager"] < 1:
        missing_parts.append("manager evaluation")
    
    if counts["peer"] < min_peers:
        missing_parts.append(f"at least {min_peers} peer evaluations (has {counts['peer']})")
    
    if counts["direct_report"] < min_direct_reports:
        missing_parts.append(
            f"at least {min_direct_reports} direct report evaluations (has {counts['direct_report']})"
        )
    
    if missing_parts:
        reason = "Missing: " + ", ".join(missing_parts)
        return False, reason
    
    return True, None


def aggregate_competency_scores(
    evaluations: Sequence[EvaluationEntity],
) -> dict[UUID, dict]:
    """
    Aggregate competency scores from multiple evaluations into a consolidated profile.
    
    For each skill/competency:
    - Calculate overall average score
    - Calculate averages by evaluator relationship
    - Count number of evaluations per relationship
    - Calculate confidence based on n and variance (optional)
    
    This implements Step 3 from flows.md: Aggregation of results in user_skill_scores
    
    Args:
        evaluations: Sequence of evaluation entities (domain objects)
        
    Returns:
        Dictionary mapping skill_id to aggregated statistics:
        {
            skill_id: {
                "overall_avg": float,
                "self_avg": Optional[float],
                "peer_avg": Optional[float],
                "manager_avg": Optional[float],
                "direct_report_avg": Optional[float],
                "n_self": int,
                "n_peer": int,
                "n_manager": int,
                "n_direct_report": int,
                "raw_stats": dict  # for JSONB storage
            }
        }
    """
    # Collect scores by skill and relationship
    scores_by_skill: dict[UUID, dict[str, list[float]]] = {}
    
    for evaluation in evaluations:
        # Only process submitted evaluations
        if not evaluation.is_submitted():  # Use domain method
            continue
        
        rel = evaluation.evaluator_relationship
        
        # Process each competency score in the evaluation
        for comp_score in evaluation.competency_scores:
            skill_id = comp_score.skill_id
            score = comp_score.score
            
            if skill_id not in scores_by_skill:
                scores_by_skill[skill_id] = {
                    "self": [],
                    "peer": [],
                    "manager": [],
                    "direct_report": [],
                }
            
            scores_by_skill[skill_id][rel].append(score)
    
    # Aggregate statistics for each skill
    aggregated = {}
    
    for skill_id, scores_by_rel in scores_by_skill.items():
        # Calculate averages per relationship
        self_scores = scores_by_rel["self"]
        peer_scores = scores_by_rel["peer"]
        manager_scores = scores_by_rel["manager"]
        direct_report_scores = scores_by_rel["direct_report"]
        
        self_avg = sum(self_scores) / len(self_scores) if self_scores else None
        peer_avg = sum(peer_scores) / len(peer_scores) if peer_scores else None
        manager_avg = sum(manager_scores) / len(manager_scores) if manager_scores else None
        direct_report_avg = (
            sum(direct_report_scores) / len(direct_report_scores)
            if direct_report_scores
            else None
        )
        
        # Calculate overall average (from all submitted scores)
        all_scores = (
            self_scores + peer_scores + manager_scores + direct_report_scores
        )
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        # Calculate confidence (simple heuristic: based on total number of scores)
        # More sophisticated: could use variance, but this is a start
        total_n = len(all_scores)
        if total_n >= 5:
            confidence = 0.9
        elif total_n >= 3:
            confidence = 0.7
        elif total_n >= 1:
            confidence = 0.5
        else:
            confidence = 0.0
        
        # Build raw_stats for JSONB storage
        raw_stats = {
            "self_scores": self_scores,
            "peer_scores": peer_scores,
            "manager_scores": manager_scores,
            "direct_report_scores": direct_report_scores,
            "self_avg": self_avg,
            "peer_avg": peer_avg,
            "manager_avg": manager_avg,
            "direct_report_avg": direct_report_avg,
            "n_self": len(self_scores),
            "n_peer": len(peer_scores),
            "n_manager": len(manager_scores),
            "n_direct_report": len(direct_report_scores),
        }
        
        aggregated[skill_id] = {
            "overall_avg": overall_avg,
            "self_avg": self_avg,
            "peer_avg": peer_avg,
            "manager_avg": manager_avg,
            "direct_report_avg": direct_report_avg,
            "n_self": len(self_scores),
            "n_peer": len(peer_scores),
            "n_manager": len(manager_scores),
            "n_direct_report": len(direct_report_scores),
            "confidence": confidence,
            "raw_stats": raw_stats,
        }
    
    return aggregated
