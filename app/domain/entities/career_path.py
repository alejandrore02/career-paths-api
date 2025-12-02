"""Domain entities for career path aggregate."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class DevelopmentAction:
    """Domain value object for a development action.
    
    Represents a specific learning activity to build skills.
    """
    action_type: str  # course, project, mentoring, shadowing, certification
    title: str
    skill_id: Optional[UUID] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    url: Optional[str] = None
    estimated_effort_hours: Optional[int] = None
    
    def is_course(self) -> bool:
        """Check if action is a course."""
        return self.action_type == "course"
    
    def is_project(self) -> bool:
        """Check if action is a project."""
        return self.action_type == "project"
    
    def is_mentoring(self) -> bool:
        """Check if action is mentoring."""
        return self.action_type == "mentoring"


@dataclass
class CareerPathStep:
    """Domain entity for a career path step.
    
    Represents a milestone in career progression.
    """
    step_number: int
    target_role_id: Optional[UUID]
    step_name: Optional[str]
    description: Optional[str]
    duration_months: Optional[int]
    actions: list[DevelopmentAction] = field(default_factory=list)
    
    def total_effort_hours(self) -> int:
        """Calculate total estimated effort hours for all actions."""
        return sum(
            action.estimated_effort_hours or 0
            for action in self.actions
        )
    
    def has_actions(self) -> bool:
        """Check if step has development actions."""
        return len(self.actions) > 0
    
    def get_actions_by_type(self, action_type: str) -> list[DevelopmentAction]:
        """Get actions of a specific type."""
        return [action for action in self.actions if action.action_type == action_type]


@dataclass
class CareerPathEntity:
    """Domain entity for career path.
    
    Represents a recommended career progression route with steps and actions.
    """
    id: UUID
    user_id: UUID
    skills_assessment_id: Optional[UUID]
    path_name: str
    recommended: bool
    feasibility_score: float
    total_duration_months: Optional[int]
    status: str  # draft, proposed, accepted, rejected
    steps: list[CareerPathStep] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate feasibility score range."""
        if not 0.0 <= self.feasibility_score <= 1.0:
            raise ValueError(f"Feasibility score must be between 0 and 1, got {self.feasibility_score}")
    
    def is_accepted(self) -> bool:
        """Check if path has been accepted by user."""
        return self.status == "accepted"
    
    def is_proposed(self) -> bool:
        """Check if path is in proposed state."""
        return self.status == "proposed"
    
    def is_draft(self) -> bool:
        """Check if path is in draft state."""
        return self.status == "draft"
    
    def is_highly_feasible(self) -> bool:
        """Check if path is highly feasible (>= 0.75)."""
        return self.feasibility_score >= 0.75
    
    def total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.steps)
    
    def get_step(self, step_number: int) -> Optional[CareerPathStep]:
        """Get a specific step by number."""
        return next(
            (step for step in self.steps if step.step_number == step_number),
            None
        )
    
    def total_development_actions(self) -> int:
        """Count total development actions across all steps."""
        return sum(len(step.actions) for step in self.steps)
    
    def estimated_total_effort_hours(self) -> int:
        """Calculate total estimated effort across all steps."""
        return sum(step.total_effort_hours() for step in self.steps)
