"""Tests for the office space calculator."""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.models.project import Project
from src.models.department import Department
from src.models.space_standards import SpaceType, DEFAULT_SPACE_STANDARDS
from src.calculator.space_calculator import SpaceCalculator
from src.calculator.remote_work_analyzer import RemoteWorkAnalyzer
from src.storage.project_storage import ProjectStorage


class TestSpaceCalculator:
    """Test the space calculator."""

    def test_basic_calculation(self):
        """Test basic space calculation."""
        project = Project(
            id="test-project",
            company_name="Test Company",
        )

        dept = Department(name="Engineering")
        dept.add_staff("Engineers", 10, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        calc = SpaceCalculator(project)
        result = calc.calculate()

        # 10 engineers × 64 SF = 640 SF workspace
        assert result.summary.total_workspace_sf == 640
        assert result.summary.total_headcount == 10

    def test_mixed_workspace_types(self):
        """Test calculation with mixed workspace types."""
        project = Project(
            id="test-project",
            company_name="Test Company",
        )

        dept = Department(name="Management")
        dept.add_staff("Executives", 2, SpaceType.PRIVATE_OFFICE_LARGE)  # 2 × 225 = 450
        dept.add_staff("Managers", 5, SpaceType.PRIVATE_OFFICE_MEDIUM)  # 5 × 150 = 750
        dept.add_staff("Staff", 10, SpaceType.WORKSTATION_STANDARD)  # 10 × 64 = 640
        project.add_department(dept)

        calc = SpaceCalculator(project)
        result = calc.calculate()

        expected_workspace = 450 + 750 + 640  # 1840 SF
        assert result.summary.total_workspace_sf == expected_workspace
        assert result.summary.total_headcount == 17

    def test_circulation_factor(self):
        """Test circulation factor calculation."""
        project = Project(
            id="test-project",
            company_name="Test Company",
            circulation_factor=0.30,  # 30%
        )

        dept = Department(name="Team")
        dept.add_staff("Staff", 10, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        calc = SpaceCalculator(project)
        result = calc.calculate()

        net_usable = 640  # 10 × 64 SF
        expected_circulation = net_usable * 0.30  # 192 SF
        expected_usable = net_usable + expected_circulation  # 832 SF

        assert result.summary.net_usable_sf == net_usable
        assert result.summary.circulation_sf == expected_circulation
        assert result.summary.usable_sf == expected_usable

    def test_loss_factor(self):
        """Test loss factor for rentable SF."""
        project = Project(
            id="test-project",
            company_name="Test Company",
            circulation_factor=0.30,
            loss_factor=0.15,  # 15%
        )

        dept = Department(name="Team")
        dept.add_staff("Staff", 10, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        calc = SpaceCalculator(project)
        result = calc.calculate()

        usable = 640 * 1.30  # 832 SF
        expected_rentable = usable * 1.15  # 956.8 SF

        assert abs(result.summary.rentable_sf - expected_rentable) < 0.01

    def test_auto_allocate_support(self):
        """Test automatic support space allocation."""
        project = Project(
            id="test-project",
            company_name="Test Company",
        )

        dept = Department(name="Company")
        dept.add_staff("Staff", 100, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        calc = SpaceCalculator(project)
        calc.auto_allocate_support_spaces()

        # Should have allocated various support spaces
        assert len(project.support_spaces) > 0

        # Check that meeting rooms were allocated
        space_types = [s.space_type for s in project.support_spaces]
        assert SpaceType.CONFERENCE_LARGE in space_types
        assert SpaceType.CONFERENCE_MEDIUM in space_types
        assert SpaceType.HUDDLE_ROOM in space_types

        # Check that mail room was allocated
        assert SpaceType.MAIL_ROOM in space_types

    def test_sf_per_person(self):
        """Test SF per person calculation."""
        project = Project(
            id="test-project",
            company_name="Test Company",
            circulation_factor=0.30,
        )

        dept = Department(name="Team")
        dept.add_staff("Staff", 10, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        calc = SpaceCalculator(project)
        result = calc.calculate()

        # 640 SF workspace + 30% circulation = 832 SF
        # 832 / 10 = 83.2 SF/person
        expected_sf_per_person = 83.2
        assert abs(result.summary.sf_per_person - expected_sf_per_person) < 0.01


class TestRemoteWorkAnalyzer:
    """Test the remote work analyzer."""

    def test_analyze_scenarios(self):
        """Test analyzing all remote work scenarios."""
        project = Project(
            id="test-project",
            company_name="Test Company",
        )

        dept = Department(name="Company")
        dept.add_staff("Staff", 50, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        calc = SpaceCalculator(project)
        calc.auto_allocate_support_spaces()

        analyzer = RemoteWorkAnalyzer(project)
        scenarios = analyzer.analyze_all_scenarios()

        assert len(scenarios) == 6  # 6 pre-defined scenarios

        # Each subsequent scenario should have more reduction
        for i in range(1, len(scenarios)):
            assert scenarios[i].workspace_reduction_percent >= scenarios[i-1].workspace_reduction_percent

    def test_custom_scenario(self):
        """Test creating a custom remote work scenario."""
        project = Project(
            id="test-project",
            company_name="Test Company",
        )

        dept = Department(name="Company")
        dept.add_staff("Staff", 50, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        calc = SpaceCalculator(project)
        calc.auto_allocate_support_spaces()

        analyzer = RemoteWorkAnalyzer(project)
        scenario = analyzer.create_custom_scenario(
            name="Custom 40%",
            remote_percentage=40,
        )

        assert scenario.remote_percentage == 40
        assert scenario.baseline_usable_sf > 0
        assert scenario.adjusted_usable_sf < scenario.baseline_usable_sf


class TestProjectStorage:
    """Test project storage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = ProjectStorage(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_save_and_load(self):
        """Test saving and loading a project."""
        project = Project(
            id="test-save-load",
            company_name="Test Company",
            location="Test Location",
        )

        dept = Department(name="Team")
        dept.add_staff("Staff", 5, SpaceType.WORKSTATION_STANDARD)
        project.add_department(dept)

        # Save
        self.storage.save(project)

        # Load
        loaded = self.storage.load("test-save-load")

        assert loaded is not None
        assert loaded.company_name == "Test Company"
        assert loaded.location == "Test Location"
        assert len(loaded.departments) == 1
        assert loaded.departments[0].total_headcount == 5

    def test_list_projects(self):
        """Test listing projects."""
        # Create multiple projects
        for i in range(3):
            project = Project(
                id=f"test-list-{i}",
                company_name=f"Company {i}",
            )
            self.storage.save(project)

        projects = self.storage.list_projects()
        assert len(projects) == 3

    def test_delete_project(self):
        """Test deleting a project."""
        project = Project(
            id="test-delete",
            company_name="Delete Me",
        )
        self.storage.save(project)

        assert self.storage.exists("test-delete")
        self.storage.delete("test-delete")
        assert not self.storage.exists("test-delete")


class TestSpaceStandards:
    """Test space standards."""

    def test_all_standards_defined(self):
        """Test that all space types have standards."""
        for space_type in SpaceType:
            assert space_type in DEFAULT_SPACE_STANDARDS

    def test_standard_sizes_reasonable(self):
        """Test that standard sizes are reasonable."""
        for space_type, standard in DEFAULT_SPACE_STANDARDS.items():
            assert standard.square_feet > 0
            assert standard.square_feet < 1000  # No single space > 1000 SF
            assert standard.name != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
