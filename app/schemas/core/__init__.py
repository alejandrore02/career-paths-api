"""Core schemas module."""

from app.schemas.core.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserSummary,
)
from app.schemas.core.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
)
from app.schemas.core.skill import (
    SkillBase,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserSummary",
    # Role
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    # Skill
    "SkillBase",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
]
