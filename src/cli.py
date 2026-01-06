#!/usr/bin/env python3
"""Command-line interface for Office Space Calculator."""

import sys
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm

from .models.project import Project
from .models.department import Department
from .models.space_standards import SpaceType, DEFAULT_SPACE_STANDARDS
from .calculator.space_calculator import SpaceCalculator
from .calculator.remote_work_analyzer import RemoteWorkAnalyzer, REMOTE_WORK_SCENARIOS
from .storage.project_storage import ProjectStorage, generate_project_id
from .export.pdf_exporter import PDFExporter
from .export.excel_exporter import ExcelExporter

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Office Space Calculator - Programming tool for architecture firms.

    Calculate office space requirements based on staff counts, departmental needs,
    and industry-standard space allocations.
    """
    pass


@main.command()
@click.option("--name", "-n", prompt="Company name", help="Company or client name")
@click.option("--location", "-l", default="", help="Project location/address")
@click.option("--project", "-p", default="", help="Project name (optional)")
@click.option("--prepared-by", "-b", default="", help="Prepared by (your name)")
def new(name: str, location: str, project: str, prepared_by: str):
    """Create a new space programming project."""
    project_id = generate_project_id(name)

    proj = Project(
        id=project_id,
        company_name=name,
        project_name=project,
        location=location,
        prepared_by=prepared_by,
    )

    storage = ProjectStorage()
    file_path = storage.save(proj)

    console.print(Panel(
        f"[green]Project created successfully![/green]\n\n"
        f"ID: [bold]{project_id}[/bold]\n"
        f"Company: {name}\n"
        f"Location: {location or 'Not specified'}\n"
        f"Saved to: {file_path}",
        title="New Project"
    ))

    if Confirm.ask("Would you like to add departments now?"):
        _add_departments_interactive(proj)
        storage.save(proj)


@main.command()
def list():
    """List all saved projects."""
    storage = ProjectStorage()
    projects = storage.list_projects()

    if not projects:
        console.print("[yellow]No projects found. Create one with 'space-calc new'[/yellow]")
        return

    table = Table(title="Saved Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Company")
    table.add_column("Location")
    table.add_column("Headcount", justify="right")
    table.add_column("Updated")

    for p in projects:
        updated = p.get("updated_at", "")[:10] if p.get("updated_at") else ""
        table.add_row(
            p["id"][:30] + "..." if len(p["id"]) > 30 else p["id"],
            p["company_name"],
            p.get("location", "")[:20],
            str(p.get("headcount", 0)),
            updated
        )

    console.print(table)


@main.command()
@click.argument("project_id")
def load(project_id: str):
    """Load and display a project's details."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    _display_project_summary(project)


@main.command("add-dept")
@click.argument("project_id")
@click.option("--name", "-n", prompt="Department name", help="Department name")
def add_department(project_id: str, name: str):
    """Add a department to a project."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    dept = Department(name=name)
    _add_staff_to_department(dept)

    project.add_department(dept)
    storage.save(project)

    console.print(f"[green]Department '{name}' added with {dept.total_headcount} staff.[/green]")


@main.command("add-staff")
@click.argument("project_id")
@click.argument("department_name")
def add_staff(project_id: str, department_name: str):
    """Add staff positions to an existing department."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    dept = project.get_department_by_name(department_name)
    if not dept:
        console.print(f"[red]Department '{department_name}' not found.[/red]")
        return

    _add_staff_to_department(dept)
    storage.save(project)

    console.print(f"[green]Staff added. Department now has {dept.total_headcount} total staff.[/green]")


@main.command("auto-support")
@click.argument("project_id")
def auto_allocate_support(project_id: str):
    """Auto-allocate support spaces based on headcount."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    if project.total_headcount == 0:
        console.print("[yellow]No staff defined. Add departments first.[/yellow]")
        return

    calc = SpaceCalculator(project)
    calc.auto_allocate_support_spaces()
    storage.save(project)

    console.print(f"[green]Support spaces auto-allocated for {project.total_headcount} employees.[/green]")
    console.print(f"Added {len(project.support_spaces)} support space allocations.")


@main.command()
@click.argument("project_id")
@click.option("--circulation", "-c", type=float, default=None, help="Circulation factor (e.g., 0.30 for 30%)")
@click.option("--loss-factor", "-l", type=float, default=None, help="Loss factor for rentable SF (e.g., 0.15)")
def calculate(project_id: str, circulation: float, loss_factor: float):
    """Calculate space requirements for a project."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    if project.total_headcount == 0:
        console.print("[yellow]No staff defined. Add departments first.[/yellow]")
        return

    if circulation is not None:
        project.circulation_factor = circulation
    if loss_factor is not None:
        project.loss_factor = loss_factor

    # Auto-allocate support if not done
    if not project.support_spaces:
        if Confirm.ask("No support spaces defined. Auto-allocate based on headcount?", default=True):
            calc = SpaceCalculator(project)
            calc.auto_allocate_support_spaces()

    calc = SpaceCalculator(project)
    result = calc.calculate()

    storage.save(project)

    _display_calculation_results(result)


@main.command("remote-analysis")
@click.argument("project_id")
def remote_analysis(project_id: str):
    """Analyze remote work impact on space requirements."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    if project.total_headcount == 0:
        console.print("[yellow]No staff defined. Add departments first.[/yellow]")
        return

    # Ensure support spaces exist
    if not project.support_spaces:
        calc = SpaceCalculator(project)
        calc.auto_allocate_support_spaces()

    analyzer = RemoteWorkAnalyzer(project)
    scenarios = analyzer.analyze_all_scenarios()

    _display_remote_analysis(scenarios)

    # Option for custom scenario
    if Confirm.ask("\nWould you like to analyze a custom remote work percentage?"):
        pct = FloatPrompt.ask("Enter remote work percentage (0-100)", default="50")
        custom = analyzer.create_custom_scenario(
            name="Custom Scenario",
            remote_percentage=float(pct),
        )
        console.print(f"\n[bold]Custom Scenario Results:[/bold]")
        console.print(f"  Baseline: {custom.baseline_usable_sf:,.0f} SF")
        console.print(f"  Adjusted: {custom.adjusted_usable_sf:,.0f} SF")
        console.print(f"  Reduction: {custom.sf_reduction:,.0f} SF ({custom.sf_reduction/custom.baseline_usable_sf*100:.1f}%)")
        console.print(f"  Est. Annual Savings: ${custom.cost_savings_estimate:,.0f}")


@main.command()
@click.argument("project_id")
@click.option("--format", "-f", "fmt", type=click.Choice(["pdf", "excel", "xlsx", "all"]), default="all", help="Export format")
@click.option("--output-dir", "-o", type=click.Path(), default=".", help="Output directory")
@click.option("--include-remote", "-r", is_flag=True, help="Include remote work analysis")
def export(project_id: str, fmt: str, output_dir: str, include_remote: bool):
    """Export project to PDF and/or Excel."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    if project.total_headcount == 0:
        console.print("[yellow]No staff defined. Cannot generate meaningful report.[/yellow]")
        return

    # Ensure support spaces
    if not project.support_spaces:
        calc = SpaceCalculator(project)
        calc.auto_allocate_support_spaces()

    calc = SpaceCalculator(project)
    result = calc.calculate()

    # Get remote scenarios if requested
    remote_scenarios = None
    if include_remote:
        analyzer = RemoteWorkAnalyzer(project)
        remote_scenarios = analyzer.analyze_all_scenarios()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    exported = []

    if fmt in ["pdf", "all"]:
        pdf_exporter = PDFExporter(output_path)
        pdf_path = pdf_exporter.export(result, include_remote_analysis=include_remote, remote_scenarios=remote_scenarios)
        exported.append(("PDF", pdf_path))

    if fmt in ["excel", "xlsx", "all"]:
        excel_exporter = ExcelExporter(output_path)
        xlsx_path = excel_exporter.export(result, include_remote_analysis=include_remote, remote_scenarios=remote_scenarios)
        exported.append(("Excel", xlsx_path))

    console.print(Panel(
        "\n".join([f"[green]✓[/green] {name}: {path}" for name, path in exported]),
        title="Export Complete"
    ))


@main.command()
@click.argument("project_id")
@click.option("--circulation", "-c", type=float, help="Circulation factor (0.25-0.40)")
@click.option("--loss-factor", "-l", type=float, help="Loss/add-on factor (0.10-0.20)")
def settings(project_id: str, circulation: float, loss_factor: float):
    """Update project calculation settings."""
    storage = ProjectStorage()
    project = storage.load(project_id)

    if not project:
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    if circulation is not None:
        if 0 <= circulation <= 1:
            project.circulation_factor = circulation
            console.print(f"[green]Circulation factor set to {circulation*100:.0f}%[/green]")
        else:
            console.print("[red]Circulation factor must be between 0 and 1[/red]")

    if loss_factor is not None:
        if 0 <= loss_factor <= 0.5:
            project.loss_factor = loss_factor
            console.print(f"[green]Loss factor set to {loss_factor*100:.0f}%[/green]")
        else:
            console.print("[red]Loss factor must be between 0 and 0.5[/red]")

    storage.save(project)


@main.command()
@click.argument("project_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(project_id: str, yes: bool):
    """Delete a project."""
    storage = ProjectStorage()

    if not storage.exists(project_id):
        console.print(f"[red]Project '{project_id}' not found.[/red]")
        return

    if not yes and not Confirm.ask(f"Are you sure you want to delete project '{project_id}'?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    storage.delete(project_id)
    console.print(f"[green]Project '{project_id}' deleted.[/green]")


@main.command()
def standards():
    """Display standard space sizes."""
    table = Table(title="Standard Space Sizes")
    table.add_column("Space Type", style="cyan")
    table.add_column("Size (SF)", justify="right")
    table.add_column("Capacity", justify="right")
    table.add_column("Description")

    for space_type, standard in DEFAULT_SPACE_STANDARDS.items():
        table.add_row(
            standard.name,
            f"{standard.square_feet:,.0f}",
            str(standard.capacity) if standard.capacity else "-",
            standard.description
        )

    console.print(table)


@main.command()
def quick():
    """Quick calculation without saving (interactive)."""
    console.print(Panel("Quick Space Estimate Calculator", style="bold blue"))

    company = Prompt.ask("Company name", default="Quick Estimate")
    headcount = IntPrompt.ask("Total headcount")

    # Simple department distribution
    project = Project(
        id="quick-estimate",
        company_name=company,
    )

    # Create default department distribution
    dept = Department(name="General")

    # Executive (5%)
    exec_count = max(1, int(headcount * 0.05))
    dept.add_staff("Executives", exec_count, SpaceType.PRIVATE_OFFICE_LARGE)

    # Managers (10%)
    mgr_count = max(1, int(headcount * 0.10))
    dept.add_staff("Managers", mgr_count, SpaceType.PRIVATE_OFFICE_MEDIUM)

    # Senior staff (15%)
    senior_count = max(1, int(headcount * 0.15))
    dept.add_staff("Senior Staff", senior_count, SpaceType.PRIVATE_OFFICE_SMALL)

    # Regular staff (70%)
    staff_count = headcount - exec_count - mgr_count - senior_count
    dept.add_staff("Staff", max(0, staff_count), SpaceType.WORKSTATION_STANDARD)

    project.add_department(dept)

    # Ask about remote work
    if Confirm.ask("Apply remote work reduction?", default=False):
        remote_pct = FloatPrompt.ask("Average remote work percentage", default="30")
        for staff in dept.staff:
            staff.remote_percentage = float(remote_pct)
        project.apply_remote_work_reduction = True

    # Set factors
    project.circulation_factor = 0.30  # Standard
    if Confirm.ask("Include loss factor for rentable SF?", default=True):
        project.loss_factor = 0.15  # Class A typical

    # Auto-allocate support
    calc = SpaceCalculator(project)
    calc.auto_allocate_support_spaces()

    # Calculate
    result = calc.calculate()

    _display_calculation_results(result)

    # Option to save
    if Confirm.ask("\nWould you like to save this project?"):
        location = Prompt.ask("Location", default="")
        project.id = generate_project_id(company)
        project.location = location
        storage = ProjectStorage()
        storage.save(project)
        console.print(f"[green]Saved as: {project.id}[/green]")


# Helper functions

def _add_departments_interactive(project: Project):
    """Interactively add departments to a project."""
    while True:
        dept_name = Prompt.ask("Department name (or 'done' to finish)")
        if dept_name.lower() == "done":
            break

        dept = Department(name=dept_name)
        _add_staff_to_department(dept)
        project.add_department(dept)
        console.print(f"[green]Added {dept_name} with {dept.total_headcount} staff.[/green]")


def _add_staff_to_department(dept: Department):
    """Interactively add staff positions to a department."""
    console.print("\n[bold]Available workspace types:[/bold]")
    workspace_types = [
        ("1", SpaceType.PRIVATE_OFFICE_LARGE, "Large Private Office (225 SF)"),
        ("2", SpaceType.PRIVATE_OFFICE_MEDIUM, "Medium Private Office (150 SF)"),
        ("3", SpaceType.PRIVATE_OFFICE_SMALL, "Small Private Office (100 SF)"),
        ("4", SpaceType.WORKSTATION_LARGE, "Large Workstation (80 SF)"),
        ("5", SpaceType.WORKSTATION_STANDARD, "Standard Workstation (64 SF)"),
        ("6", SpaceType.WORKSTATION_COMPACT, "Compact Workstation (48 SF)"),
        ("7", SpaceType.HOTELING_STATION, "Hoteling Station (42 SF)"),
    ]

    for num, _, desc in workspace_types:
        console.print(f"  {num}. {desc}")

    while True:
        role = Prompt.ask("\nRole/title (or 'done' to finish)")
        if role.lower() == "done":
            break

        count = IntPrompt.ask("Number of people")
        ws_choice = Prompt.ask("Workspace type (1-7)", default="5")

        try:
            space_type = workspace_types[int(ws_choice) - 1][1]
        except (ValueError, IndexError):
            space_type = SpaceType.WORKSTATION_STANDARD

        remote = FloatPrompt.ask("Remote work % (0-100)", default="0")

        dept.add_staff(role, count, space_type, float(remote))
        console.print(f"[dim]Added {count} {role}(s)[/dim]")


def _display_project_summary(project: Project):
    """Display a project summary."""
    console.print(Panel(
        f"Company: [bold]{project.company_name}[/bold]\n"
        f"Project: {project.project_name or '-'}\n"
        f"Location: {project.location or '-'}\n"
        f"Headcount: {project.total_headcount}\n"
        f"Departments: {len(project.departments)}\n"
        f"Circulation Factor: {project.circulation_factor*100:.0f}%\n"
        f"Loss Factor: {project.loss_factor*100:.0f}%",
        title=f"Project: {project.id}"
    ))

    if project.departments:
        table = Table(title="Departments")
        table.add_column("Department")
        table.add_column("Headcount", justify="right")
        table.add_column("Roles", justify="right")

        for dept in project.departments:
            table.add_row(dept.name, str(dept.total_headcount), str(len(dept.staff)))

        console.print(table)


def _display_calculation_results(result: CalculationResult):
    """Display calculation results."""
    summary = result.summary

    # Main summary
    console.print(Panel(
        f"[bold]Total Headcount:[/bold] {summary.total_headcount}\n"
        f"[bold]Effective On-Site:[/bold] {summary.effective_onsite:.1f}\n\n"
        f"[bold cyan]Net Usable Area:[/bold cyan] {summary.net_usable_sf:,.0f} SF\n"
        f"  Workspaces: {summary.total_workspace_sf:,.0f} SF\n"
        f"  Meeting Spaces: {summary.total_meeting_sf:,.0f} SF\n"
        f"  Support Spaces: {summary.total_support_sf:,.0f} SF\n\n"
        f"[bold]Circulation ({summary.circulation_factor*100:.0f}%):[/bold] {summary.circulation_sf:,.0f} SF\n"
        f"[bold green]Total Usable Area:[/bold green] {summary.usable_sf:,.0f} SF\n\n"
        + (f"[bold]Loss Factor ({summary.loss_factor*100:.0f}%):[/bold]\n"
           f"[bold yellow]Total Rentable Area:[/bold yellow] {summary.rentable_sf:,.0f} SF\n\n"
           if summary.loss_factor > 0 else "")
        + f"[dim]Usable SF/Person: {summary.sf_per_person:,.0f}[/dim]"
        + (f"\n[dim]Rentable SF/Person: {summary.sf_per_person_rentable:,.0f}[/dim]" if summary.loss_factor > 0 else ""),
        title="Space Calculation Results"
    ))

    # Department breakdown
    if result.department_workspace_sf:
        table = Table(title="Department Breakdown")
        table.add_column("Department")
        table.add_column("Headcount", justify="right")
        table.add_column("Workspace SF", justify="right")

        for dept_name in result.department_headcount:
            table.add_row(
                dept_name,
                str(result.department_headcount[dept_name]),
                f"{result.department_workspace_sf.get(dept_name, 0):,.0f}"
            )

        console.print(table)


def _display_remote_analysis(scenarios: list):
    """Display remote work analysis results."""
    table = Table(title="Remote Work Impact Analysis")
    table.add_column("Scenario")
    table.add_column("Remote %", justify="right")
    table.add_column("Days/Week", justify="right")
    table.add_column("Usable SF", justify="right")
    table.add_column("Reduction", justify="right")
    table.add_column("Savings/Year", justify="right")

    for s in scenarios:
        reduction_pct = (s.baseline_usable_sf - s.adjusted_usable_sf) / s.baseline_usable_sf * 100 if s.baseline_usable_sf > 0 else 0
        table.add_row(
            s.name,
            f"{s.remote_percentage:.0f}%",
            f"{s.days_in_office_per_week:.1f}",
            f"{s.adjusted_usable_sf:,.0f}",
            f"{reduction_pct:.0f}%",
            f"${s.cost_savings_estimate:,.0f}"
        )

    console.print(table)


if __name__ == "__main__":
    main()
