"""
PDF Report Generator
Creates branded Rhône Risk policy analysis reports
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from config import settings

logger = logging.getLogger(__name__)


# Rhône Risk Brand Colors
BRAND_PRIMARY = colors.HexColor("#162B4D")  # Dark navy
BRAND_ACCENT = colors.HexColor("#0CBDDB")   # Cyan/teal
BRAND_LIGHT = colors.HexColor("#F5F7FA")    # Light gray background
BRAND_SUCCESS = colors.HexColor("#28A745")  # Green
BRAND_WARNING = colors.HexColor("#FFC107")  # Yellow
BRAND_DANGER = colors.HexColor("#DC3545")   # Red


@dataclass
class ReportResult:
    """Result of report generation"""
    success: bool
    report_path: Optional[str] = None
    error: Optional[str] = None


class ReportGenerator:
    """
    Generates professionally branded PDF reports from analysis data.
    """

    def __init__(self):
        self.styles = self._create_styles()

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for the report"""
        base_styles = getSampleStyleSheet()

        styles = {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=base_styles['Title'],
                fontSize=28,
                textColor=BRAND_PRIMARY,
                spaceAfter=30,
                alignment=TA_CENTER,
            ),
            'heading1': ParagraphStyle(
                'CustomH1',
                parent=base_styles['Heading1'],
                fontSize=18,
                textColor=BRAND_PRIMARY,
                spaceBefore=20,
                spaceAfter=12,
                borderWidth=0,
                borderColor=BRAND_ACCENT,
                borderPadding=5,
            ),
            'heading2': ParagraphStyle(
                'CustomH2',
                parent=base_styles['Heading2'],
                fontSize=14,
                textColor=BRAND_PRIMARY,
                spaceBefore=15,
                spaceAfter=8,
            ),
            'body': ParagraphStyle(
                'CustomBody',
                parent=base_styles['Normal'],
                fontSize=10,
                leading=14,
                spaceAfter=8,
            ),
            'metric': ParagraphStyle(
                'Metric',
                parent=base_styles['Normal'],
                fontSize=24,
                textColor=BRAND_PRIMARY,
                alignment=TA_CENTER,
            ),
            'metric_label': ParagraphStyle(
                'MetricLabel',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=colors.gray,
                alignment=TA_CENTER,
            ),
            'recommendation': ParagraphStyle(
                'Recommendation',
                parent=base_styles['Normal'],
                fontSize=16,
                textColor=colors.white,
                alignment=TA_CENTER,
                backColor=BRAND_PRIMARY,
            ),
            'bullet': ParagraphStyle(
                'Bullet',
                parent=base_styles['Normal'],
                fontSize=10,
                leftIndent=20,
                bulletIndent=10,
                spaceAfter=4,
            ),
            'footer': ParagraphStyle(
                'Footer',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.gray,
                alignment=TA_CENTER,
            ),
        }

        return styles

    async def generate_report(
        self,
        analysis_data: Dict[str, Any],
        output_dir: str = "reports",
    ) -> ReportResult:
        """
        Generate a branded PDF report from analysis data.

        Args:
            analysis_data: Structured analysis output from Claude
            output_dir: Directory to save the report

        Returns:
            ReportResult with path to generated PDF
        """
        client_name = analysis_data.get("client_company", "Unknown Client")
        logger.info(f"📄 Generating report for {client_name}")

        os.makedirs(output_dir, exist_ok=True)

        # Create filename
        safe_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_Policy_Analysis_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        try:
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
            )

            # Build the report content
            story = []

            # Cover Page
            story.extend(self._create_cover_page(analysis_data))
            story.append(PageBreak())

            # Executive Summary
            story.extend(self._create_executive_summary(analysis_data))
            story.append(PageBreak())

            # Coverage Analysis
            story.extend(self._create_coverage_analysis(analysis_data))
            story.append(PageBreak())

            # Red Flags & Deficiencies
            story.extend(self._create_red_flags_section(analysis_data))

            # Recommendations
            story.extend(self._create_recommendations_section(analysis_data))

            # Build the PDF
            doc.build(story)

            logger.info(f"✅ Report generated: {filepath}")

            return ReportResult(
                success=True,
                report_path=filepath,
            )

        except Exception as e:
            logger.error(f"❌ Report generation failed: {str(e)}")
            return ReportResult(
                success=False,
                error=str(e),
            )

    def _create_cover_page(self, data: Dict[str, Any]) -> list:
        """Create the report cover page"""
        elements = []

        # Add some top spacing
        elements.append(Spacer(1, 1.5*inch))

        # Company branding
        elements.append(Paragraph(
            "RHÔNE RISK ADVISORY",
            self.styles['metric_label']
        ))

        elements.append(Spacer(1, 0.3*inch))

        # Report title
        elements.append(Paragraph(
            "Cyber Insurance",
            self.styles['title']
        ))
        elements.append(Paragraph(
            "Policy Analysis Report",
            ParagraphStyle(
                'Subtitle',
                fontSize=20,
                textColor=BRAND_ACCENT,
                alignment=TA_CENTER,
                spaceAfter=40,
            )
        ))

        # Horizontal rule
        elements.append(HRFlowable(
            width="80%",
            thickness=2,
            color=BRAND_ACCENT,
            spaceBefore=20,
            spaceAfter=40,
        ))

        # Client info
        client_name = data.get("client_company", "Unknown Client")
        client_industry = data.get("client_industry", "N/A")
        analysis_date = data.get("analysis_date", datetime.now().strftime("%B %d, %Y"))

        elements.append(Paragraph(
            f"<b>Prepared for:</b> {client_name}",
            ParagraphStyle('ClientInfo', fontSize=14, alignment=TA_CENTER, spaceAfter=8)
        ))
        elements.append(Paragraph(
            f"<b>Industry:</b> {client_industry}",
            ParagraphStyle('ClientInfo', fontSize=12, alignment=TA_CENTER, spaceAfter=8)
        ))
        elements.append(Paragraph(
            f"<b>Analysis Date:</b> {analysis_date}",
            ParagraphStyle('ClientInfo', fontSize=12, alignment=TA_CENTER, spaceAfter=40)
        ))

        # Overall score display
        exec_summary = data.get("executive_summary", {})
        key_metrics = exec_summary.get("key_metrics", {})
        overall_score = key_metrics.get("overall_maturity_score", "N/A")
        recommendation = exec_summary.get("recommendation", "REVIEW REQUIRED")

        elements.append(Spacer(1, 0.5*inch))

        # Score box
        score_table = Table([
            [Paragraph(f"{overall_score}", self.styles['metric'])],
            [Paragraph("Overall Maturity Score", self.styles['metric_label'])],
        ], colWidths=[3*inch])

        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
            ('BOX', (0, 0), (-1, -1), 2, BRAND_ACCENT),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        elements.append(score_table)

        elements.append(Spacer(1, 0.3*inch))

        # Recommendation badge
        rec_color = self._get_recommendation_color(recommendation)
        elements.append(Paragraph(
            f"<b>Recommendation: {recommendation}</b>",
            ParagraphStyle(
                'RecBadge',
                fontSize=14,
                textColor=colors.white,
                backColor=rec_color,
                alignment=TA_CENTER,
                spaceBefore=10,
                spaceAfter=10,
                borderPadding=10,
            )
        ))

        return elements

    def _create_executive_summary(self, data: Dict[str, Any]) -> list:
        """Create executive summary section"""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['heading1']))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_ACCENT))

        exec_summary = data.get("executive_summary", {})

        # Overview paragraph
        overview = exec_summary.get("overview", "No overview available.")
        elements.append(Paragraph(overview, self.styles['body']))

        elements.append(Spacer(1, 0.3*inch))

        # Key metrics table
        key_metrics = exec_summary.get("key_metrics", {})
        metrics_data = [
            ["Overall Score", f"{key_metrics.get('overall_maturity_score', 'N/A')}/10"],
            ["Coverage Comprehensiveness", f"{key_metrics.get('coverage_comprehensiveness', 'N/A')}%"],
            ["Total Coverage Limit", f"${key_metrics.get('total_coverage_limit', 0):,}"],
            ["Annual Premium", f"${key_metrics.get('annual_premium', 0):,}"],
            ["Carrier Rating", key_metrics.get('primary_carrier_rating', 'N/A')],
        ]

        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), BRAND_LIGHT),
            ('TEXTCOLOR', (0, 0), (-1, -1), BRAND_PRIMARY),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(metrics_table)

        elements.append(Spacer(1, 0.3*inch))

        # Critical action items
        action_items = exec_summary.get("critical_action_items", [])
        if action_items:
            elements.append(Paragraph("Critical Action Items", self.styles['heading2']))
            for item in action_items:
                elements.append(Paragraph(
                    f"• {item}",
                    self.styles['bullet']
                ))

        # Recommendation rationale
        rationale = exec_summary.get("recommendation_rationale", "")
        if rationale:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Recommendation Rationale", self.styles['heading2']))
            elements.append(Paragraph(rationale, self.styles['body']))

        return elements

    def _create_coverage_analysis(self, data: Dict[str, Any]) -> list:
        """Create detailed coverage analysis section"""
        elements = []

        elements.append(Paragraph("Coverage Analysis", self.styles['heading1']))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_ACCENT))

        coverage_analysis = data.get("coverage_analysis", {})

        # First-party coverages
        first_party = coverage_analysis.get("first_party", [])
        if first_party:
            elements.append(Paragraph("First-Party Coverages", self.styles['heading2']))
            elements.append(self._create_coverage_table(first_party))

        elements.append(Spacer(1, 0.3*inch))

        # Third-party coverages
        third_party = coverage_analysis.get("third_party", [])
        if third_party:
            elements.append(Paragraph("Third-Party Coverages", self.styles['heading2']))
            elements.append(self._create_coverage_table(third_party))

        return elements

    def _create_coverage_table(self, coverages: list) -> Table:
        """Create a table for coverage items"""
        headers = ["Coverage", "Score", "Sublimit", "Notes"]
        data = [headers]

        for cov in coverages:
            score = cov.get("maturity_score", "N/A")
            score_display = f"{score}/10" if isinstance(score, (int, float)) else str(score)

            data.append([
                cov.get("coverage_name", "Unknown"),
                score_display,
                cov.get("sublimit", "N/A"),
                cov.get("notes", "")[:100] + "..." if len(cov.get("notes", "")) > 100 else cov.get("notes", ""),
            ])

        table = Table(data, colWidths=[2*inch, 0.8*inch, 1.2*inch, 2.5*inch])
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),

            # Body styling
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),

            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ]))

        return table

    def _create_red_flags_section(self, data: Dict[str, Any]) -> list:
        """Create red flags and deficiencies section"""
        elements = []

        elements.append(Paragraph("Critical Findings", self.styles['heading1']))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_DANGER))

        red_flags = data.get("red_flags", [])
        policy_summary = data.get("policy_summary", {})

        # Red flags
        if red_flags:
            elements.append(Paragraph("Red Flags", self.styles['heading2']))
            for flag in red_flags:
                severity = flag.get("severity", "MEDIUM")
                severity_color = BRAND_DANGER if severity == "HIGH" else BRAND_WARNING

                elements.append(Paragraph(
                    f"<font color='{severity_color.hexval()}'>[{severity}]</font> {flag.get('flag', '')}",
                    self.styles['bullet']
                ))
                if flag.get("impact"):
                    elements.append(Paragraph(
                        f"   Impact: {flag.get('impact')}",
                        ParagraphStyle('Impact', fontSize=9, textColor=colors.gray, leftIndent=30)
                    ))

        # Critical deficiencies
        deficiencies = policy_summary.get("critical_deficiencies", [])
        if deficiencies:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Critical Deficiencies", self.styles['heading2']))
            for item in deficiencies:
                elements.append(Paragraph(f"• {item}", self.styles['bullet']))

        # Moderate concerns
        concerns = policy_summary.get("moderate_concerns", [])
        if concerns:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Moderate Concerns", self.styles['heading2']))
            for item in concerns:
                elements.append(Paragraph(f"• {item}", self.styles['bullet']))

        return elements

    def _create_recommendations_section(self, data: Dict[str, Any]) -> list:
        """Create recommendations section"""
        elements = []

        elements.append(Paragraph("Recommendations", self.styles['heading1']))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_SUCCESS))

        recommendations = data.get("recommendations", {})

        # Immediate actions
        immediate = recommendations.get("immediate_actions", [])
        if immediate:
            elements.append(Paragraph("Immediate Actions", self.styles['heading2']))
            for action in immediate:
                priority = action.get("priority", "")
                item = action.get("item", "")
                rationale = action.get("rationale", "")

                elements.append(Paragraph(
                    f"<b>{priority}. {item}</b>",
                    self.styles['bullet']
                ))
                if rationale:
                    elements.append(Paragraph(
                        f"   {rationale}",
                        ParagraphStyle('Rationale', fontSize=9, textColor=colors.gray, leftIndent=30)
                    ))

        # Renewal considerations
        renewal = recommendations.get("renewal_considerations", [])
        if renewal:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Renewal Considerations", self.styles['heading2']))
            for item in renewal:
                elements.append(Paragraph(f"• {item}", self.styles['bullet']))

        # Risk management suggestions
        risk_mgmt = recommendations.get("risk_management_suggestions", [])
        if risk_mgmt:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Risk Management Suggestions", self.styles['heading2']))
            for item in risk_mgmt:
                elements.append(Paragraph(f"• {item}", self.styles['bullet']))

        # Footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        elements.append(Paragraph(
            f"This report was prepared by Rhône Risk Advisory. "
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}.",
            self.styles['footer']
        ))

        return elements

    def _get_recommendation_color(self, recommendation: str) -> colors.Color:
        """Get color for recommendation badge"""
        rec_upper = recommendation.upper()
        if "BIND" in rec_upper and "CONDITIONS" not in rec_upper:
            return BRAND_SUCCESS
        elif "CONDITIONS" in rec_upper or "NEGOTIATE" in rec_upper:
            return BRAND_WARNING
        else:
            return BRAND_DANGER


# Module-level instance
generator = ReportGenerator()
