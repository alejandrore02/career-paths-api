"""Domain entities for evaluation aggregate."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class CompetencyScore:
    """Domain value object for a competency score.
    
    Immutable value object representing a single skill rating.
    Contains business logic for score validation and comparison.
    """
    skill_id: UUID
    score: float
    comments: Optional[str] = None
    
    def __post_init__(self):
        """Validate score range."""
        if not 0.0 <= self.score <= 10.0:
            raise ValueError(f"Score must be between 0 and 10, got {self.score}")
    
    def is_high_score(self) -> bool:
        """Check if score is considered high (>= 8.0)."""
        return self.score >= 8.0
    
    def is_low_score(self) -> bool:
        """Check if score is considered low (<= 5.0)."""
        return self.score <= 5.0


@dataclass
class EvaluationEntity:
    """Domain entity for evaluation (360° feedback).
    
    Rich domain model with business logic for evaluation state and behavior.
    Separates business rules from persistence concerns.
    """
    id: UUID
    user_id: UUID
    evaluation_cycle_id: UUID
    evaluator_id: UUID
    evaluator_relationship: str
    status: str
    competency_scores: list[CompetencyScore] = field(default_factory=list)
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_submitted(self) -> bool:
        """Check if evaluation has been submitted."""
        return self.status == "submitted"
    
    def is_pending(self) -> bool:
        """Check if evaluation is still pending."""
        return self.status == "pending"
    
    def has_competency(self, skill_id: UUID) -> bool:
        """Check if evaluation includes a specific skill."""
        return any(score.skill_id == skill_id for score in self.competency_scores)
    
    def get_competency_score(self, skill_id: UUID) -> Optional[CompetencyScore]:
        """Get score for a specific skill."""
        return next(
            (score for score in self.competency_scores if score.skill_id == skill_id),
            None
        )
    
    def average_score(self) -> float:
        """Calculate average score across all competencies."""
        if not self.competency_scores:
            return 0.0
        return sum(score.score for score in self.competency_scores) / len(self.competency_scores)
    
    def is_self_evaluation(self) -> bool:
        """Check if this is a self-evaluation."""
        return self.evaluator_relationship == "self"
    
    def is_peer_evaluation(self) -> bool:
        """Check if this is a peer evaluation."""
        return self.evaluator_relationship == "peer"
    
    def is_manager_evaluation(self) -> bool:
        """Check if this is a manager evaluation."""
        return self.evaluator_relationship == "manager"
    
    def is_direct_report_evaluation(self) -> bool:
        """Check if this is a direct report evaluation."""
        return self.evaluator_relationship == "direct_report"
