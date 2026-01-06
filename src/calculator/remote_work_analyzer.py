"""Remote work impact analyzer for office space programming."""

from dataclasses import dataclass
from typing import Optional
from ..models.project import Project
from ..models.space_standards import SpaceType
from .space_calculator import SpaceCalculator, CalculationResult


@dataclass
class RemoteWorkScenario:
    """A remote work scenario with calculated impact."""

    name: str
    description: str
    remote_percentage: float  # Overall remote work percentage
    days_in_office_per_week: float  # Average days in office

    # Space reduction potential
    workspace_reduction_percent: float
    meeting_space_adjustment: str  # "increase", "same", "decrease"
    hoteling_ratio: float  # Employees per hoteling station

    # Calculated results (filled in after analysis)
    baseline_usable_sf: float = 0
    adjusted_usable_sf: float = 0
    sf_reduction: float = 0
    cost_savings_estimate: float = 0  # Assuming $50/SF/year


# Pre-defined scenarios
REMOTE_WORK_SCENARIOS = [
    RemoteWorkScenario(
        name="Traditional Office",
        description="All employees work on-site full time",
        remote_percentage=0,
        days_in_office_per_week=5,
        workspace_reduction_percent=0,
        meeting_space_adjustment="same",
        hoteling_ratio=1.0,
    ),
    RemoteWorkScenario(
        name="Minimal Remote",
        description="Occasional remote work (1 day/week average)",
        remote_percentage=20,
        days_in_office_per_week=4,
        workspace_reduction_percent=10,
        meeting_space_adjustment="same",
        hoteling_ratio=1.5,
    ),
    RemoteWorkScenario(
        name="Hybrid Balanced",
        description="Balanced hybrid (2-3 days remote/week)",
        remote_percentage=50,
        days_in_office_per_week=2.5,
        workspace_reduction_percent=30,
        meeting_space_adjustment="increase",
        hoteling_ratio=2.5,
    ),
    RemoteWorkScenario(
        name="Hybrid Heavy Remote",
        description="Heavy remote with occasional office visits (3-4 days remote/week)",
        remote_percentage=70,
        days_in_office_per_week=1.5,
        workspace_reduction_percent=50,
        meeting_space_adjustment="increase",
        hoteling_ratio=4.0,
    ),
    RemoteWorkScenario(
        name="Remote First",
        description="Remote-first with hoteling stations (4+ days remote/week)",
        remote_percentage=85,
        days_in_office_per_week=0.75,
        workspace_reduction_percent=65,
        meeting_space_adjustment="increase",
        hoteling_ratio=6.0,
    ),
    RemoteWorkScenario(
        name="Fully Remote",
        description="Fully remote with collaboration space only",
        remote_percentage=95,
        days_in_office_per_week=0.25,
        workspace_reduction_percent=80,
        meeting_space_adjustment="same",
        hoteling_ratio=10.0,
    ),
]


class RemoteWorkAnalyzer:
    """Analyzes the impact of remote work policies on space requirements."""

    # Cost assumptions
    COST_PER_SF_ANNUAL = 50.0  # $/SF/year (varies by market)

    def __init__(self, project: Project):
        """Initialize analyzer with a project."""
        self.project = project

    def analyze_scenario(
        self,
        scenario: RemoteWorkScenario,
        baseline_result: Optional[CalculationResult] = None
    ) -> RemoteWorkScenario:
        """Analyze a specific remote work scenario."""
        # Get baseline (no remote work reduction)
        if baseline_result is None:
            self.project.apply_remote_work_reduction = False
            calc = SpaceCalculator(self.project)
            baseline_result = calc.calculate()

        scenario.baseline_usable_sf = baseline_result.summary.usable_sf

        # Calculate adjusted SF based on reduction percentage
        reduction_factor = 1 - (scenario.workspace_reduction_percent / 100)
        workspace_sf = baseline_result.summary.total_workspace_sf * reduction_factor

        # Adjust meeting space based on scenario
        meeting_sf = baseline_result.summary.total_meeting_sf
        if scenario.meeting_space_adjustment == "increase":
            meeting_sf *= 1.15  # 15% more meeting space for hybrid
        elif scenario.meeting_space_adjustment == "decrease":
            meeting_sf *= 0.85

        # Support space adjusts slightly with workspace
        support_sf = baseline_result.summary.total_support_sf * (0.7 + 0.3 * reduction_factor)

        # Calculate adjusted totals
        net_usable = workspace_sf + meeting_sf + support_sf
        circulation = net_usable * self.project.circulation_factor
        scenario.adjusted_usable_sf = net_usable + circulation

        # Calculate savings
        scenario.sf_reduction = scenario.baseline_usable_sf - scenario.adjusted_usable_sf
        scenario.cost_savings_estimate = scenario.sf_reduction * self.COST_PER_SF_ANNUAL

        return scenario

    def analyze_all_scenarios(self) -> list[RemoteWorkScenario]:
        """Analyze all pre-defined remote work scenarios."""
        # Get baseline once
        self.project.apply_remote_work_reduction = False
        calc = SpaceCalculator(self.project)
        baseline = calc.calculate()

        results = []
        for scenario_template in REMOTE_WORK_SCENARIOS:
            # Create a copy to avoid modifying templates
            scenario = RemoteWorkScenario(
                name=scenario_template.name,
                description=scenario_template.description,
                remote_percentage=scenario_template.remote_percentage,
                days_in_office_per_week=scenario_template.days_in_office_per_week,
                workspace_reduction_percent=scenario_template.workspace_reduction_percent,
                meeting_space_adjustment=scenario_template.meeting_space_adjustment,
                hoteling_ratio=scenario_template.hoteling_ratio,
            )
            results.append(self.analyze_scenario(scenario, baseline))

        return results

    def create_custom_scenario(
        self,
        name: str,
        remote_percentage: float,
        hoteling_ratio: float = 3.0,
        description: str = ""
    ) -> RemoteWorkScenario:
        """Create and analyze a custom remote work scenario."""
        # Estimate reduction based on remote percentage
        if remote_percentage <= 20:
            reduction = remote_percentage * 0.5
            meeting_adj = "same"
        elif remote_percentage <= 50:
            reduction = 10 + (remote_percentage - 20) * 0.67
            meeting_adj = "increase"
        elif remote_percentage <= 80:
            reduction = 30 + (remote_percentage - 50) * 0.67
            meeting_adj = "increase"
        else:
            reduction = 50 + (remote_percentage - 80) * 1.5
            meeting_adj = "same"

        days_in_office = 5 * (1 - remote_percentage / 100)

        scenario = RemoteWorkScenario(
            name=name,
            description=description or f"Custom scenario with {remote_percentage}% remote work",
            remote_percentage=remote_percentage,
            days_in_office_per_week=days_in_office,
            workspace_reduction_percent=min(reduction, 85),
            meeting_space_adjustment=meeting_adj,
            hoteling_ratio=hoteling_ratio,
        )

        return self.analyze_scenario(scenario)

    def get_recommendations(self, target_reduction_percent: float) -> dict:
        """Get recommendations to achieve a target space reduction."""
        scenarios = self.analyze_all_scenarios()

        # Find scenarios that meet or exceed target
        viable = [s for s in scenarios if s.workspace_reduction_percent >= target_reduction_percent]

        if not viable:
            return {
                "achievable": False,
                "message": f"Target reduction of {target_reduction_percent}% exceeds maximum feasible reduction",
                "max_reduction": max(s.workspace_reduction_percent for s in scenarios),
                "recommended_scenario": scenarios[-1],  # Most aggressive
            }

        # Find the least aggressive scenario that meets target
        recommended = min(viable, key=lambda s: s.workspace_reduction_percent)

        return {
            "achievable": True,
            "recommended_scenario": recommended,
            "alternative_scenarios": [s for s in viable if s != recommended],
            "implementation_notes": self._get_implementation_notes(recommended),
        }

    def _get_implementation_notes(self, scenario: RemoteWorkScenario) -> list[str]:
        """Get implementation notes for a scenario."""
        notes = []

        if scenario.remote_percentage > 0:
            notes.append(f"Implement {scenario.remote_percentage}% remote work policy")

        if scenario.hoteling_ratio > 1:
            notes.append(
                f"Convert assigned desks to hoteling stations at {scenario.hoteling_ratio}:1 ratio"
            )

        if scenario.meeting_space_adjustment == "increase":
            notes.append("Increase meeting room quantity by 15% to support hybrid collaboration")
            notes.append("Ensure all meeting rooms have video conferencing capability")

        if scenario.days_in_office_per_week < 3:
            notes.append("Implement desk booking system for hoteling stations")
            notes.append("Consider neighborhood/team-based seating arrangements")

        if scenario.workspace_reduction_percent > 30:
            notes.append("Add more phone booths and focus rooms for privacy")
            notes.append("Increase collaboration/lounge areas")

        if scenario.workspace_reduction_percent > 50:
            notes.append("Consider activity-based working (ABW) model")
            notes.append("Implement lockers for personal item storage")

        return notes

    def calculate_roi(
        self,
        scenario: RemoteWorkScenario,
        current_lease_rate: float,
        implementation_cost: float = 0
    ) -> dict:
        """Calculate ROI for implementing a remote work scenario."""
        annual_savings = scenario.sf_reduction * current_lease_rate
        payback_months = 0

        if annual_savings > 0 and implementation_cost > 0:
            payback_months = (implementation_cost / annual_savings) * 12

        return {
            "annual_savings": annual_savings,
            "sf_reduction": scenario.sf_reduction,
            "implementation_cost": implementation_cost,
            "payback_months": payback_months,
            "five_year_savings": (annual_savings * 5) - implementation_cost,
            "ten_year_savings": (annual_savings * 10) - implementation_cost,
        }
