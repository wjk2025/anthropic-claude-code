"""Department and staff member models for office programming."""

from typing import Optional
from pydantic import BaseModel, Field
from .space_standards import SpaceType


class StaffMember(BaseModel):
    """Represents a staff position/role with space requirements."""

    role: str = Field(description="Job title or role name")
    count: int = Field(ge=0, description="Number of people in this role")
    space_type: SpaceType = Field(description="Type of workspace assigned")
    remote_percentage: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Percentage of time working remotely (0-100)"
    )
    notes: str = Field(default="", description="Additional notes")

    @property
    def effective_onsite_count(self) -> float:
        """Calculate effective on-site headcount accounting for remote work."""
        return self.count * (1 - self.remote_percentage / 100)


class Department(BaseModel):
    """Represents a department with staff and space requirements."""

    name: str = Field(description="Department name")
    staff: list[StaffMember] = Field(default_factory=list, description="Staff positions")

    # Department-specific support spaces (beyond standard allocation)
    additional_spaces: dict[SpaceType, int] = Field(
        default_factory=dict,
        description="Additional dedicated spaces for this department (type -> quantity)"
    )

    notes: str = Field(default="", description="Department notes")

    @property
    def total_headcount(self) -> int:
        """Total number of staff in the department."""
        return sum(s.count for s in self.staff)

    @property
    def effective_onsite_headcount(self) -> float:
        """Effective on-site headcount accounting for remote work."""
        return sum(s.effective_onsite_count for s in self.staff)

    def get_space_type_counts(self) -> dict[SpaceType, int]:
        """Get count of each workspace type needed."""
        counts: dict[SpaceType, int] = {}
        for staff in self.staff:
            if staff.space_type in counts:
                counts[staff.space_type] += staff.count
            else:
                counts[staff.space_type] = staff.count
        return counts

    def get_effective_space_type_counts(self) -> dict[SpaceType, float]:
        """Get effective count of each workspace type accounting for remote work."""
        counts: dict[SpaceType, float] = {}
        for staff in self.staff:
            effective = staff.effective_onsite_count
            if staff.space_type in counts:
                counts[staff.space_type] += effective
            else:
                counts[staff.space_type] = effective
        return counts

    def add_staff(
        self,
        role: str,
        count: int,
        space_type: SpaceType,
        remote_percentage: float = 0.0,
        notes: str = ""
    ) -> None:
        """Add a staff position to the department."""
        self.staff.append(StaffMember(
            role=role,
            count=count,
            space_type=space_type,
            remote_percentage=remote_percentage,
            notes=notes
        ))


def create_sample_department(name: str, headcount: int) -> Department:
    """Create a sample department with typical role distribution."""
    dept = Department(name=name)

    # Typical distribution for a generic department
    if headcount >= 10:
        # Department head (large office)
        dept.add_staff("Director", 1, SpaceType.PRIVATE_OFFICE_LARGE)
        # Managers (medium offices)
        manager_count = max(1, headcount // 8)
        dept.add_staff("Manager", manager_count, SpaceType.PRIVATE_OFFICE_MEDIUM)
        # Senior staff (small offices or large workstations)
        senior_count = max(1, headcount // 5)
        dept.add_staff("Senior Staff", senior_count, SpaceType.PRIVATE_OFFICE_SMALL)
        # Regular staff (standard workstations)
        regular_count = headcount - 1 - manager_count - senior_count
        dept.add_staff("Staff", max(0, regular_count), SpaceType.WORKSTATION_STANDARD)
    elif headcount >= 5:
        dept.add_staff("Manager", 1, SpaceType.PRIVATE_OFFICE_MEDIUM)
        dept.add_staff("Staff", headcount - 1, SpaceType.WORKSTATION_STANDARD)
    else:
        dept.add_staff("Staff", headcount, SpaceType.WORKSTATION_STANDARD)

    return dept
