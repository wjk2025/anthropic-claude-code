#!/usr/bin/env python3
"""Demo script showing the Office Space Calculator in action."""

from pathlib import Path
from src.models.project import Project
from src.models.department import Department
from src.models.space_standards import SpaceType
from src.calculator.space_calculator import SpaceCalculator
from src.calculator.remote_work_analyzer import RemoteWorkAnalyzer
from src.storage.project_storage import ProjectStorage, generate_project_id
from src.export.pdf_exporter import PDFExporter
from src.export.excel_exporter import ExcelExporter


def main():
    """Run a complete demo of the office space calculator."""
    print("=" * 60)
    print("OFFICE SPACE CALCULATOR - DEMO")
    print("=" * 60)

    # Create a sample project
    project = Project(
        id=generate_project_id("Acme Corporation"),
        company_name="Acme Corporation",
        project_name="Headquarters Relocation",
        location="123 Main Street, New York, NY 10001",
        prepared_by="Demo User",
        circulation_factor=0.30,  # 30% circulation
        loss_factor=0.15,  # 15% loss factor (Class A building)
    )

    print(f"\n📋 Created project: {project.company_name}")
    print(f"   Location: {project.location}")

    # Add departments
    print("\n📊 Adding departments...")

    # Executive department
    exec_dept = Department(name="Executive")
    exec_dept.add_staff("CEO", 1, SpaceType.PRIVATE_OFFICE_LARGE)
    exec_dept.add_staff("C-Suite", 4, SpaceType.PRIVATE_OFFICE_LARGE)
    exec_dept.add_staff("Executive Assistants", 5, SpaceType.WORKSTATION_STANDARD)
    project.add_department(exec_dept)
    print(f"   ✓ Executive: {exec_dept.total_headcount} staff")

    # Engineering department
    eng_dept = Department(name="Engineering")
    eng_dept.add_staff("VP Engineering", 1, SpaceType.PRIVATE_OFFICE_MEDIUM)
    eng_dept.add_staff("Engineering Managers", 4, SpaceType.PRIVATE_OFFICE_MEDIUM)
    eng_dept.add_staff("Senior Engineers", 15, SpaceType.PRIVATE_OFFICE_SMALL)
    eng_dept.add_staff("Software Engineers", 40, SpaceType.WORKSTATION_STANDARD, remote_percentage=20)
    project.add_department(eng_dept)
    print(f"   ✓ Engineering: {eng_dept.total_headcount} staff")

    # Sales department
    sales_dept = Department(name="Sales")
    sales_dept.add_staff("VP Sales", 1, SpaceType.PRIVATE_OFFICE_MEDIUM)
    sales_dept.add_staff("Sales Managers", 3, SpaceType.PRIVATE_OFFICE_SMALL)
    sales_dept.add_staff("Sales Representatives", 20, SpaceType.WORKSTATION_STANDARD, remote_percentage=40)
    project.add_department(sales_dept)
    print(f"   ✓ Sales: {sales_dept.total_headcount} staff")

    # Marketing department
    mkt_dept = Department(name="Marketing")
    mkt_dept.add_staff("VP Marketing", 1, SpaceType.PRIVATE_OFFICE_MEDIUM)
    mkt_dept.add_staff("Marketing Managers", 2, SpaceType.PRIVATE_OFFICE_SMALL)
    mkt_dept.add_staff("Marketing Staff", 12, SpaceType.WORKSTATION_STANDARD)
    project.add_department(mkt_dept)
    print(f"   ✓ Marketing: {mkt_dept.total_headcount} staff")

    # Operations department
    ops_dept = Department(name="Operations")
    ops_dept.add_staff("VP Operations", 1, SpaceType.PRIVATE_OFFICE_MEDIUM)
    ops_dept.add_staff("Operations Managers", 2, SpaceType.PRIVATE_OFFICE_SMALL)
    ops_dept.add_staff("Operations Staff", 15, SpaceType.WORKSTATION_COMPACT)
    project.add_department(ops_dept)
    print(f"   ✓ Operations: {ops_dept.total_headcount} staff")

    # HR & Finance
    hr_dept = Department(name="HR & Finance")
    hr_dept.add_staff("CFO", 1, SpaceType.PRIVATE_OFFICE_LARGE)
    hr_dept.add_staff("HR Director", 1, SpaceType.PRIVATE_OFFICE_MEDIUM)
    hr_dept.add_staff("HR Staff", 6, SpaceType.WORKSTATION_STANDARD)
    hr_dept.add_staff("Finance Staff", 8, SpaceType.WORKSTATION_STANDARD)
    project.add_department(hr_dept)
    print(f"   ✓ HR & Finance: {hr_dept.total_headcount} staff")

    print(f"\n   Total Headcount: {project.total_headcount}")

    # Auto-allocate support spaces
    print("\n🏢 Auto-allocating support spaces...")
    calc = SpaceCalculator(project)
    calc.auto_allocate_support_spaces()
    print(f"   Allocated {len(project.support_spaces)} support space types")

    # Calculate space requirements
    print("\n📐 Calculating space requirements...")
    result = calc.calculate()
    summary = result.summary

    print(f"\n{'=' * 60}")
    print("SPACE CALCULATION RESULTS")
    print("=" * 60)

    print(f"\nHeadcount:")
    print(f"   Total: {summary.total_headcount}")
    print(f"   Effective On-Site: {summary.effective_onsite:.1f}")

    print(f"\nSpace Breakdown:")
    print(f"   Workspaces:     {summary.total_workspace_sf:>10,.0f} SF")
    print(f"   Meeting Spaces: {summary.total_meeting_sf:>10,.0f} SF")
    print(f"   Support Spaces: {summary.total_support_sf:>10,.0f} SF")
    print(f"   {'─' * 30}")
    print(f"   Net Usable:     {summary.net_usable_sf:>10,.0f} SF")

    print(f"\nCirculation ({summary.circulation_factor*100:.0f}%):")
    print(f"   Circulation:    {summary.circulation_sf:>10,.0f} SF")
    print(f"   {'─' * 30}")
    print(f"   USABLE TOTAL:   {summary.usable_sf:>10,.0f} SF")

    print(f"\nLoss Factor ({summary.loss_factor*100:.0f}%):")
    print(f"   {'─' * 30}")
    print(f"   RENTABLE TOTAL: {summary.rentable_sf:>10,.0f} SF")

    print(f"\nEfficiency Metrics:")
    print(f"   Usable SF/Person:   {summary.sf_per_person:,.0f} SF")
    print(f"   Rentable SF/Person: {summary.sf_per_person_rentable:,.0f} SF")

    # Remote work analysis
    print(f"\n{'=' * 60}")
    print("REMOTE WORK IMPACT ANALYSIS")
    print("=" * 60)

    analyzer = RemoteWorkAnalyzer(project)
    scenarios = analyzer.analyze_all_scenarios()

    print(f"\n{'Scenario':<20} {'Remote %':>10} {'Usable SF':>12} {'Reduction':>10} {'Savings/Yr':>12}")
    print("-" * 66)
    for s in scenarios:
        reduction_pct = (s.baseline_usable_sf - s.adjusted_usable_sf) / s.baseline_usable_sf * 100 if s.baseline_usable_sf > 0 else 0
        print(f"{s.name:<20} {s.remote_percentage:>9.0f}% {s.adjusted_usable_sf:>11,.0f} {reduction_pct:>9.0f}% ${s.cost_savings_estimate:>10,.0f}")

    # Save project
    print(f"\n{'=' * 60}")
    print("SAVING PROJECT")
    print("=" * 60)

    storage = ProjectStorage()
    file_path = storage.save(project)
    print(f"\n   ✓ Project saved to: {file_path}")

    # Export reports
    print(f"\n{'=' * 60}")
    print("EXPORTING REPORTS")
    print("=" * 60)

    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)

    # PDF Export
    pdf_exporter = PDFExporter(output_dir)
    pdf_path = pdf_exporter.export(result, include_remote_analysis=True, remote_scenarios=scenarios)
    print(f"\n   ✓ PDF Report: {pdf_path}")

    # Excel Export
    excel_exporter = ExcelExporter(output_dir)
    xlsx_path = excel_exporter.export(result, include_remote_analysis=True, remote_scenarios=scenarios)
    print(f"   ✓ Excel Report: {xlsx_path}")

    print(f"\n{'=' * 60}")
    print("DEMO COMPLETE!")
    print("=" * 60)
    print(f"\nReports have been saved to the ./output directory.")
    print(f"Project data saved to: {file_path}")


if __name__ == "__main__":
    main()
