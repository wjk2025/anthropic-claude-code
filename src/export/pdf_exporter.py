"""PDF export functionality for office space reports."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from ..calculator.space_calculator import CalculationResult
from ..calculator.remote_work_analyzer import RemoteWorkScenario


class PDFExporter:
    """Exports space program calculations to PDF format."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize exporter with optional output directory."""
        self.output_dir = output_dir or Path(".")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle",
            parent=self.styles["Normal"],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.grey,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#2c3e50"),
        ))
        self.styles.add(ParagraphStyle(
            name="TableHeader",
            parent=self.styles["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
        ))
        self.styles.add(ParagraphStyle(
            name="Footer",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        ))

    def _format_number(self, value: float, decimals: int = 0) -> str:
        """Format a number with thousand separators."""
        if decimals == 0:
            return f"{value:,.0f}"
        return f"{value:,.{decimals}f}"

    def _create_table_style(self, has_header: bool = True) -> TableStyle:
        """Create a standard table style."""
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),  # Right-align last column (numbers)
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]
        return TableStyle(style_commands)

    def export(
        self,
        result: CalculationResult,
        filename: Optional[str] = None,
        include_remote_analysis: bool = False,
        remote_scenarios: Optional[list[RemoteWorkScenario]] = None,
    ) -> Path:
        """Export calculation results to PDF."""
        project = result.project

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c if c.isalnum() else "_" for c in project.company_name)
            filename = f"space_program_{safe_name}_{timestamp}.pdf"

        output_path = self.output_dir / filename
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=LETTER,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Title page content
        story.append(Paragraph("OFFICE SPACE PROGRAM", self.styles["ReportTitle"]))
        story.append(Paragraph(project.company_name, self.styles["Heading1"]))
        if project.project_name:
            story.append(Paragraph(project.project_name, self.styles["ReportSubtitle"]))
        if project.location:
            story.append(Paragraph(project.location, self.styles["ReportSubtitle"]))
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            f"Prepared: {datetime.now().strftime('%B %d, %Y')}",
            self.styles["ReportSubtitle"]
        ))
        if project.prepared_by:
            story.append(Paragraph(f"By: {project.prepared_by}", self.styles["ReportSubtitle"]))
        story.append(Spacer(1, 40))

        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles["SectionHeader"]))
        summary = result.summary

        summary_data = [
            ["Metric", "Value"],
            ["Total Headcount", str(summary.total_headcount)],
            ["Effective On-Site", f"{summary.effective_onsite:.1f}"],
            ["Net Usable Area", f"{self._format_number(summary.net_usable_sf)} SF"],
            ["Circulation Factor", f"{summary.circulation_factor * 100:.0f}%"],
            ["Circulation Area", f"{self._format_number(summary.circulation_sf)} SF"],
            ["Total Usable Area", f"{self._format_number(summary.usable_sf)} SF"],
        ]

        if summary.loss_factor > 0:
            summary_data.extend([
                ["Loss Factor", f"{summary.loss_factor * 100:.0f}%"],
                ["Total Rentable Area", f"{self._format_number(summary.rentable_sf)} SF"],
            ])

        summary_data.extend([
            ["Usable SF/Person", f"{self._format_number(summary.sf_per_person)} SF"],
        ])
        if summary.loss_factor > 0:
            summary_data.append(
                ["Rentable SF/Person", f"{self._format_number(summary.sf_per_person_rentable)} SF"]
            )

        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(self._create_table_style())
        story.append(summary_table)
        story.append(Spacer(1, 30))

        # Department Breakdown
        story.append(Paragraph("DEPARTMENT BREAKDOWN", self.styles["SectionHeader"]))
        dept_data = [["Department", "Headcount", "Workspace SF"]]
        for dept_name, headcount in result.department_headcount.items():
            sf = result.department_workspace_sf.get(dept_name, 0)
            dept_data.append([dept_name, str(headcount), f"{self._format_number(sf)} SF"])

        dept_data.append(["TOTAL", str(summary.total_headcount),
                          f"{self._format_number(summary.total_workspace_sf)} SF"])

        dept_table = Table(dept_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
        dept_table.setStyle(self._create_table_style())
        # Bold the total row
        dept_table.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
        ]))
        story.append(dept_table)
        story.append(Spacer(1, 30))

        # Workspace Details
        if result.workspace_counts:
            story.append(Paragraph("WORKSPACE ALLOCATION", self.styles["SectionHeader"]))
            ws_data = [["Space Type", "Count", "SF/Unit", "Total SF"]]
            for space_type, count in result.workspace_counts.items():
                if count > 0:
                    size = project.get_space_size(space_type)
                    total = count * size
                    ws_data.append([
                        space_type.replace("_", " ").title(),
                        f"{count:.1f}",
                        f"{self._format_number(size)} SF",
                        f"{self._format_number(total)} SF",
                    ])

            ws_table = Table(ws_data, colWidths=[2.5 * inch, 1 * inch, 1.25 * inch, 1.25 * inch])
            ws_table.setStyle(self._create_table_style())
            story.append(ws_table)
            story.append(Spacer(1, 30))

        # Meeting Spaces
        if summary.meeting_breakdown:
            story.append(Paragraph("MEETING SPACES", self.styles["SectionHeader"]))
            meeting_data = [["Space Type", "Quantity", "Total SF"]]
            for name, sf in summary.meeting_breakdown.items():
                qty = result.meeting_counts.get(
                    next((k for k in result.meeting_counts if k.value.replace("_", " ").title() in name.title()), None),
                    1
                )
                meeting_data.append([name, str(qty) if qty else "-", f"{self._format_number(sf)} SF"])

            meeting_data.append(["TOTAL", "", f"{self._format_number(summary.total_meeting_sf)} SF"])

            meeting_table = Table(meeting_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
            meeting_table.setStyle(self._create_table_style())
            meeting_table.setStyle(TableStyle([
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
            ]))
            story.append(meeting_table)
            story.append(Spacer(1, 30))

        # Support Spaces
        if summary.support_breakdown:
            story.append(Paragraph("SUPPORT SPACES", self.styles["SectionHeader"]))
            support_data = [["Space Type", "Total SF"]]
            for name, sf in summary.support_breakdown.items():
                support_data.append([name, f"{self._format_number(sf)} SF"])

            support_data.append(["TOTAL", f"{self._format_number(summary.total_support_sf)} SF"])

            support_table = Table(support_data, colWidths=[4 * inch, 2 * inch])
            support_table.setStyle(self._create_table_style())
            support_table.setStyle(TableStyle([
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
            ]))
            story.append(support_table)
            story.append(Spacer(1, 30))

        # Remote Work Analysis
        if include_remote_analysis and remote_scenarios:
            story.append(PageBreak())
            story.append(Paragraph("REMOTE WORK IMPACT ANALYSIS", self.styles["SectionHeader"]))
            story.append(Paragraph(
                "The following scenarios illustrate potential space reductions based on different "
                "remote work policies.",
                self.styles["Normal"]
            ))
            story.append(Spacer(1, 15))

            remote_data = [["Scenario", "Remote %", "Days/Week", "Usable SF", "Reduction"]]
            for scenario in remote_scenarios:
                reduction_pct = (
                    (scenario.baseline_usable_sf - scenario.adjusted_usable_sf)
                    / scenario.baseline_usable_sf * 100
                    if scenario.baseline_usable_sf > 0 else 0
                )
                remote_data.append([
                    scenario.name,
                    f"{scenario.remote_percentage:.0f}%",
                    f"{scenario.days_in_office_per_week:.1f}",
                    f"{self._format_number(scenario.adjusted_usable_sf)} SF",
                    f"{reduction_pct:.0f}%",
                ])

            remote_table = Table(remote_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1.25 * inch, 1 * inch])
            remote_table.setStyle(self._create_table_style())
            story.append(remote_table)

        # Footer note
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            "This space program is based on industry standard space planning guidelines. "
            "Actual requirements may vary based on specific organizational needs and local building codes.",
            self.styles["Footer"]
        ))

        # Build PDF
        doc.build(story)
        return output_path
