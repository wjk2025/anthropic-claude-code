"""Core space calculation engine for office programming."""

from dataclasses import dataclass
from typing import Optional
from ..models.project import Project, ProjectSummary
from ..models.space_standards import (
    SpaceType,
    DEFAULT_SPACE_STANDARDS,
    get_all_workspace_types,
    get_all_meeting_types,
    get_all_support_types,
)


@dataclass
class CalculationResult:
    """Detailed results from space calculation."""

    project: Project
    summary: ProjectSummary

    # Detailed breakdowns by department
    department_workspace_sf: dict[str, float]
    department_headcount: dict[str, int]

    # Space counts
    workspace_counts: dict[SpaceType, float]
    meeting_counts: dict[SpaceType, int]
    support_counts: dict[SpaceType, int]


class SpaceCalculator:
    """Calculator for office space programming."""

    # Industry standard circulation factors
    CIRCULATION_LOW = 0.25  # Efficient/dense layout
    CIRCULATION_STANDARD = 0.30  # Standard office
    CIRCULATION_HIGH = 0.35  # Generous circulation
    CIRCULATION_VERY_HIGH = 0.40  # Premium/executive space

    # Industry standard loss factors (for rentable conversion)
    LOSS_FACTOR_CLASS_A = 0.15  # Class A building typical
    LOSS_FACTOR_CLASS_B = 0.12  # Class B building typical
    LOSS_FACTOR_LOW = 0.10  # Efficient building
    LOSS_FACTOR_HIGH = 0.20  # Older/inefficient building

    def __init__(self, project: Project):
        """Initialize calculator with a project."""
        self.project = project

    def calculate(self) -> CalculationResult:
        """Perform full space calculation."""
        summary = ProjectSummary(
            circulation_factor=self.project.circulation_factor,
            loss_factor=self.project.loss_factor,
            total_headcount=self.project.total_headcount,
            effective_onsite=self.project.effective_onsite_headcount,
        )

        # Track department-level data
        dept_workspace_sf: dict[str, float] = {}
        dept_headcount: dict[str, int] = {}

        # Track space counts
        workspace_counts: dict[SpaceType, float] = {}
        meeting_counts: dict[SpaceType, int] = {}
        support_counts: dict[SpaceType, int] = {}

        workspace_types = set(get_all_workspace_types())

        # Calculate workspace areas by department
        for dept in self.project.departments:
            dept_headcount[dept.name] = dept.total_headcount
            dept_sf = 0.0

            # Get space type counts (respecting remote work if enabled)
            if self.project.apply_remote_work_reduction:
                space_counts = dept.get_effective_space_type_counts()
            else:
                space_counts = {k: float(v) for k, v in dept.get_space_type_counts().items()}

            # Calculate SF for each workspace type
            for space_type, count in space_counts.items():
                if space_type in workspace_types:
                    size = self.project.get_space_size(space_type)
                    sf = count * size
                    dept_sf += sf

                    # Track totals
                    if space_type in workspace_counts:
                        workspace_counts[space_type] += count
                    else:
                        workspace_counts[space_type] = count

                    # Track breakdown
                    type_name = DEFAULT_SPACE_STANDARDS[space_type].name
                    if type_name in summary.workspace_breakdown:
                        summary.workspace_breakdown[type_name] += sf
                    else:
                        summary.workspace_breakdown[type_name] = sf

            dept_workspace_sf[dept.name] = dept_sf

        summary.total_workspace_sf = sum(dept_workspace_sf.values())

        # Calculate meeting space areas from support allocations
        meeting_types = set(get_all_meeting_types())
        for allocation in self.project.support_spaces:
            if allocation.space_type in meeting_types:
                sf = allocation.get_total_sf()
                summary.total_meeting_sf += sf
                meeting_counts[allocation.space_type] = allocation.quantity

                type_name = DEFAULT_SPACE_STANDARDS[allocation.space_type].name
                summary.meeting_breakdown[type_name] = sf

        # Calculate support space areas
        support_types = set(get_all_support_types())
        specialty_types = {
            SpaceType.TRAINING_ROOM, SpaceType.LIBRARY,
            SpaceType.FOCUS_ROOM, SpaceType.COLLABORATION_AREA
        }

        for allocation in self.project.support_spaces:
            if allocation.space_type in support_types or allocation.space_type in specialty_types:
                sf = allocation.get_total_sf()
                summary.total_support_sf += sf
                support_counts[allocation.space_type] = allocation.quantity

                type_name = DEFAULT_SPACE_STANDARDS[allocation.space_type].name
                summary.support_breakdown[type_name] = sf

        # Calculate totals
        summary.net_usable_sf = (
            summary.total_workspace_sf +
            summary.total_meeting_sf +
            summary.total_support_sf
        )

        # Apply circulation factor
        summary.circulation_sf = summary.net_usable_sf * summary.circulation_factor
        summary.usable_sf = summary.net_usable_sf + summary.circulation_sf

        # Apply loss factor for rentable SF
        if summary.loss_factor > 0:
            summary.rentable_sf = summary.usable_sf * (1 + summary.loss_factor)
        else:
            summary.rentable_sf = summary.usable_sf

        # Calculate per-person metrics
        if summary.total_headcount > 0:
            summary.sf_per_person = summary.usable_sf / summary.total_headcount
            summary.sf_per_person_rentable = summary.rentable_sf / summary.total_headcount

        return CalculationResult(
            project=self.project,
            summary=summary,
            department_workspace_sf=dept_workspace_sf,
            department_headcount=dept_headcount,
            workspace_counts=workspace_counts,
            meeting_counts=meeting_counts,
            support_counts=support_counts,
        )

    def auto_allocate_support_spaces(self) -> None:
        """Automatically allocate support spaces based on headcount ratios."""
        headcount = self.project.total_headcount
        if headcount == 0:
            return

        # Clear existing support spaces
        self.project.support_spaces = []

        # Meeting rooms
        # Large conference: 1 per 100 employees
        large_conf = max(1, headcount // 100)
        self.project.add_support_space(SpaceType.CONFERENCE_LARGE, large_conf)

        # Medium conference: 1 per 40 employees
        med_conf = max(1, headcount // 40)
        self.project.add_support_space(SpaceType.CONFERENCE_MEDIUM, med_conf)

        # Small conference: 1 per 25 employees
        small_conf = max(1, headcount // 25)
        self.project.add_support_space(SpaceType.CONFERENCE_SMALL, small_conf)

        # Huddle rooms: 1 per 15 employees
        huddles = max(1, headcount // 15)
        self.project.add_support_space(SpaceType.HUDDLE_ROOM, huddles)

        # Phone booths: 1 per 10 employees
        booths = max(2, headcount // 10)
        self.project.add_support_space(SpaceType.PHONE_BOOTH, booths)

        # Support spaces
        self.project.add_support_space(SpaceType.RECEPTION, 1)
        self.project.add_support_space(SpaceType.WAITING_AREA, 1)

        # Break room: sized by headcount (15 SF/person, min 200 SF)
        break_sf = max(200, headcount * 15)
        self.project.add_support_space(SpaceType.BREAK_ROOM, 1, custom_size=break_sf)

        # Kitchen: 1 per floor (estimate 1 per 75 people)
        kitchens = max(1, headcount // 75)
        self.project.add_support_space(SpaceType.KITCHEN, kitchens)

        # Copy/print: 1 per 30 employees
        copy_areas = max(1, headcount // 30)
        self.project.add_support_space(SpaceType.COPY_PRINT_AREA, copy_areas)

        # Storage: sized by headcount (7 SF/person)
        storage_sf = max(100, headcount * 7)
        self.project.add_support_space(SpaceType.STORAGE, 1, custom_size=storage_sf)

        # Mail room: 1 per 200 employees (only for larger organizations)
        if headcount >= 30:
            mail_rooms = max(1, headcount // 200)
            self.project.add_support_space(SpaceType.MAIL_ROOM, mail_rooms)

        # Server/IT room
        self.project.add_support_space(SpaceType.SERVER_ROOM, 1)

        # Wellness room: 1 per 50 employees
        wellness = max(1, headcount // 50)
        self.project.add_support_space(SpaceType.WELLNESS_ROOM, wellness)

        # Focus rooms: 1 per 20 employees
        focus = max(1, headcount // 20)
        self.project.add_support_space(SpaceType.FOCUS_ROOM, focus)

        # Training room: 1 per 150 employees (for larger organizations)
        if headcount >= 50:
            training = max(1, headcount // 150)
            self.project.add_support_space(SpaceType.TRAINING_ROOM, training)

        # Collaboration area: sized by headcount (12 SF/person)
        collab_sf = max(150, headcount * 12)
        self.project.add_support_space(SpaceType.COLLABORATION_AREA, 1, custom_size=collab_sf)

    @staticmethod
    def estimate_sf_per_person(density: str = "standard") -> dict:
        """Get industry benchmark SF per person estimates."""
        benchmarks = {
            "dense": {
                "description": "High-density open office",
                "usable_sf_per_person": 125,
                "rentable_sf_per_person": 150,
            },
            "efficient": {
                "description": "Efficient modern workplace",
                "usable_sf_per_person": 150,
                "rentable_sf_per_person": 175,
            },
            "standard": {
                "description": "Standard office environment",
                "usable_sf_per_person": 175,
                "rentable_sf_per_person": 200,
            },
            "comfortable": {
                "description": "Comfortable with private offices",
                "usable_sf_per_person": 225,
                "rentable_sf_per_person": 260,
            },
            "spacious": {
                "description": "Executive/professional services",
                "usable_sf_per_person": 300,
                "rentable_sf_per_person": 350,
            },
        }
        return benchmarks.get(density, benchmarks["standard"])
