"""Data models for the office space calculator."""

from .space_standards import SpaceStandard, SpaceType, DEFAULT_SPACE_STANDARDS
from .department import Department, StaffMember
from .project import Project, ProjectSummary

__all__ = [
    "SpaceStandard",
    "SpaceType",
    "DEFAULT_SPACE_STANDARDS",
    "Department",
    "StaffMember",
    "Project",
    "ProjectSummary",
]
