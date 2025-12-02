"""Domain entities for skill profile aggregate."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class UserSkillScore:
    """Domain value object for an aggregated skill score.
    
    Represents a consolidated skill rating from multiple evaluation sources.
    """
    skill_id: UUID
    score: float
    confidence: float
    source: str
    raw_stats: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate score and confidence ranges."""
        if not 0.0 <= self.score <= 10.0:
            raise ValueError(f"Score must be between 0 and 10, got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
    
    def is_high_confidence(self) -> bool:
        """Check if confidence is high (>= 0.8)."""
        return self.confidence >= 0.8
    
    def is_strong_skill(self) -> bool:
        """Check if skill is strong (score >= 8.0 and high confidence)."""
        return self.score >= 8.0 and self.is_high_confidence()
    
    def needs_development(self) -> bool:
        """Check if skill needs development (score < 6.0)."""
        return self.score < 6.0


@dataclass
class SkillProfile:
    """Domain entity for aggregated skill profile.
    
    Consolidated view of user's skills based on 360° evaluations.
    Contains business logic for skill analysis and gap identification.
    """
    user_id: UUID
    cycle_id: UUID
    skills: list[UserSkillScore] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_skill_score(self, skill_id: UUID) -> Optional[UserSkillScore]:
        """Get score for a specific skill."""
        return next((s for s in self.skills if s.skill_id == skill_id), None)
    
    def has_skill(self, skill_id: UUID) -> bool:
        """Check if profile includes a specific skill."""
        return any(s.skill_id == skill_id for s in self.skills)
    
    def average_score(self) -> float:
        """Calculate average score across all skills."""
        if not self.skills:
            return 0.0
        return sum(s.score for s in self.skills) / len(self.skills)
    
    def average_confidence(self) -> float:
        """Calculate average confidence across all skills."""
        if not self.skills:
            return 0.0
        return sum(s.confidence for s in self.skills) / len(self.skills)
    
    def get_strengths(self, threshold: float = 8.0) -> list[UserSkillScore]:
        """Get skills above threshold (strengths)."""
        return [s for s in self.skills if s.score >= threshold]
    
    def get_development_areas(self, threshold: float = 6.0) -> list[UserSkillScore]:
        """Get skills below threshold (need development)."""
        return [s for s in self.skills if s.score < threshold]
    
    def get_high_confidence_skills(self) -> list[UserSkillScore]:
        """Get skills with high confidence (>= 0.8)."""
        return [s for s in self.skills if s.is_high_confidence()]
    
    def skill_gap(self, skill_id: UUID, target_level: float) -> Optional[float]:
        """Calculate gap between current and target level for a skill."""
        skill = self.get_skill_score(skill_id)
        if skill is None:
            return None
        return max(0.0, target_level - skill.score)
