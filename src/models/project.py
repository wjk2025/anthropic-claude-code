"""Project model for office space programming."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .department import Department
from .space_standards import SpaceType, SpaceStandard, DEFAULT_SPACE_STANDARDS


class SupportSpaceAllocation(BaseModel):
    """Tracks support space allocations for the project."""

    space_type: SpaceType
    quantity: int = Field(ge=0, description="Number of this space type")
    custom_size_sf: Optional[float] = Field(
        default=None,
        description="Custom size override (uses standard if None)"
    )
    notes: str = Field(default="", description="Notes about this allocation")

    def get_size(self) -> float:
        """Get the size per unit (custom or standard)."""
        if self.custom_size_sf is not None:
            return self.custom_size_sf
        return DEFAULT_SPACE_STANDARDS[self.space_type].square_feet

    def get_total_sf(self) -> float:
        """Get total square footage for this allocation."""
        return self.quantity * self.get_size()


class ProjectSummary(BaseModel):
    """Summary of calculated space requirements."""

    # Workspace areas
    total_workspace_sf: float = Field(default=0, description="Total workspace square footage")
    workspace_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="SF by workspace type"
    )

    # Meeting space areas
    total_meeting_sf: float = Field(default=0, description="Total meeting space square footage")
    meeting_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="SF by meeting room type"
    )

    # Support space areas
    total_support_sf: float = Field(default=0, description="Total support space square footage")
    support_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="SF by support space type"
    )

    # Totals
    net_usable_sf: float = Field(default=0, description="Net usable square footage")
    circulation_factor: float = Field(default=0.30, description="Circulation factor (e.g., 0.30 = 30%)")
    circulation_sf: float = Field(default=0, description="Circulation square footage")
    usable_sf: float = Field(default=0, description="Usable square footage (net + circulation)")

    loss_factor: float = Field(default=0.0, description="Loss/add-on factor for rentable conversion")
    rentable_sf: float = Field(default=0, description="Rentable square footage")

    # Headcount info
    total_headcount: int = Field(default=0, description="Total staff count")
    effective_onsite: float = Field(default=0, description="Effective on-site count")
    sf_per_person: float = Field(default=0, description="Usable SF per person")
    sf_per_person_rentable: float = Field(default=0, description="Rentable SF per person")


class Project(BaseModel):
    """Main project model for office space programming."""

    # Company/Project identification
    id: str = Field(description="Unique project identifier")
    company_name: str = Field(description="Company or client name")
    project_name: str = Field(default="", description="Project name (optional)")
    location: str = Field(default="", description="Project location/address")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    prepared_by: str = Field(default="", description="Person who prepared the program")
    notes: str = Field(default="", description="General project notes")

    # Departments
    departments: list[Department] = Field(
        default_factory=list,
        description="List of departments"
    )

    # Support spaces (shared across organization)
    support_spaces: list[SupportSpaceAllocation] = Field(
        default_factory=list,
        description="Support and shared spaces"
    )

    # Custom space standards (overrides defaults)
    custom_standards: dict[SpaceType, float] = Field(
        default_factory=dict,
        description="Custom SF overrides by space type"
    )

    # Calculation parameters
    circulation_factor: float = Field(
        default=0.30,
        ge=0,
        le=1,
        description="Circulation factor (industry standard: 0.25-0.35)"
    )
    loss_factor: float = Field(
        default=0.0,
        ge=0,
        le=0.5,
        description="Loss/add-on factor for rentable conversion (typically 0.10-0.20)"
    )

    # Remote work settings
    apply_remote_work_reduction: bool = Field(
        default=False,
        description="Whether to apply remote work reductions to space calculations"
    )
    hoteling_ratio: float = Field(
        default=3.0,
        ge=1,
        description="Hoteling ratio (employees per hoteling station) for remote workers"
    )

    @property
    def total_headcount(self) -> int:
        """Total headcount across all departments."""
        return sum(d.total_headcount for d in self.departments)

    @property
    def effective_onsite_headcount(self) -> float:
        """Effective on-site headcount accounting for remote work."""
        return sum(d.effective_onsite_headcount for d in self.departments)

    def get_space_size(self, space_type: SpaceType) -> float:
        """Get the size for a space type (custom or default)."""
        if space_type in self.custom_standards:
            return self.custom_standards[space_type]
        return DEFAULT_SPACE_STANDARDS[space_type].square_feet

    def add_department(self, department: Department) -> None:
        """Add a department to the project."""
        self.departments.append(department)
        self.updated_at = datetime.now()

    def add_support_space(
        self,
        space_type: SpaceType,
        quantity: int,
        custom_size: Optional[float] = None,
        notes: str = ""
    ) -> None:
        """Add a support space allocation."""
        self.support_spaces.append(SupportSpaceAllocation(
            space_type=space_type,
            quantity=quantity,
            custom_size_sf=custom_size,
            notes=notes
        ))
        self.updated_at = datetime.now()

    def set_custom_standard(self, space_type: SpaceType, size_sf: float) -> None:
        """Set a custom size for a space type."""
        self.custom_standards[space_type] = size_sf
        self.updated_at = datetime.now()

    def get_department_by_name(self, name: str) -> Optional[Department]:
        """Find a department by name."""
        for dept in self.departments:
            if dept.name.lower() == name.lower():
                return dept
        return None

    def model_dump_for_storage(self) -> dict:
        """Get a dictionary representation for JSON storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_storage(cls, data: dict) -> "Project":
        """Create a project from stored JSON data."""
        return cls.model_validate(data)
