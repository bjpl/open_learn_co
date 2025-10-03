"""PDF export formatter"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .base import BaseExporter


class PDFExporter(BaseExporter):
    """Export data to PDF format"""

    def __init__(self, export_dir: str = "exports"):
        super().__init__(export_dir)
        self.max_records = 100  # Limit for performance
        self.page_size = A4

    def get_file_extension(self) -> str:
        return "pdf"

    async def export(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export data to PDF file

        Args:
            data: List of records to export
            filename: Base filename
            metadata: Optional metadata for header

        Returns:
            Path to exported PDF file
        """
        # Sanitize and limit data
        clean_data = self.sanitize_data(data)
        if len(clean_data) > self.max_records:
            clean_data = clean_data[:self.max_records]

        # Generate filename and path
        full_filename = self.generate_filename(filename)
        file_path = self.get_file_path(full_filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=self.page_size,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )

        # Build PDF content
        story = []

        # Add header
        story.extend(self._create_header(metadata or {}))

        # Add summary statistics
        story.extend(self._create_summary(clean_data, metadata or {}))
        story.append(PageBreak())

        # Add data table
        story.extend(self._create_data_table(clean_data))

        # Build PDF
        doc.build(story)

        return str(file_path)

    def _create_header(self, metadata: Dict[str, Any]) -> List:
        """Create PDF header section"""
        styles = getSampleStyleSheet()

        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            alignment=TA_CENTER,
            spaceAfter=12
        )

        # Subtitle style
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#424242'),
            alignment=TA_CENTER,
            spaceAfter=20
        )

        story = []

        # Title
        title = metadata.get('title', 'OpenLearn Colombia - Data Export')
        story.append(Paragraph(title, title_style))

        # Export date
        export_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Exported: {export_date}", subtitle_style))

        story.append(Spacer(1, 0.3*inch))

        return story

    def _create_summary(self, data: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List:
        """Create summary statistics section"""
        styles = getSampleStyleSheet()

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=12
        )

        story = []
        story.append(Paragraph("Summary Statistics", heading_style))

        # Create summary table
        summary_data = [
            ["Metric", "Value"],
            ["Total Records", str(len(data))],
            ["Export Format", "PDF"],
            ["Page Size", "A4"],
        ]

        # Add custom metadata to summary
        if 'filters_applied' in metadata:
            filters = metadata['filters_applied']
            if isinstance(filters, dict):
                for key, value in filters.items():
                    summary_data.append([f"Filter: {key}", str(value)])

        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        return story

    def _create_data_table(self, data: List[Dict[str, Any]]) -> List:
        """Create main data table"""
        styles = getSampleStyleSheet()

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=12
        )

        story = []
        story.append(Paragraph("Detailed Records", heading_style))

        if not data:
            story.append(Paragraph("No records to display", styles['Normal']))
            return story

        # Get all unique keys from data
        all_keys = set()
        for record in data:
            all_keys.update(record.keys())

        # Limit columns for readability
        max_columns = 5
        columns = sorted(list(all_keys))[:max_columns]

        # Create table data
        table_data = [columns]  # Header row

        for record in data:
            row = []
            for col in columns:
                value = record.get(col, '')
                # Truncate long values
                str_value = str(value)[:100]
                if len(str(value)) > 100:
                    str_value += '...'
                row.append(str_value)
            table_data.append(row)

        # Calculate column widths
        available_width = 6.5 * inch
        col_width = available_width / len(columns)

        # Create table
        data_table = Table(table_data, colWidths=[col_width] * len(columns))
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(data_table)

        return story

    async def export_articles(
        self,
        articles: List[Dict[str, Any]],
        filename: str = "articles"
    ) -> str:
        """
        Export articles with custom PDF formatting

        Args:
            articles: List of article records
            filename: Base filename

        Returns:
            Path to exported PDF file
        """
        metadata = {
            'title': 'OpenLearn Colombia - Articles Export',
            'filters_applied': {'type': 'articles'}
        }

        return await self.export(articles, filename, metadata)
