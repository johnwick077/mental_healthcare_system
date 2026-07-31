from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO


def get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportTitle', fontSize=16, spaceAfter=12, alignment=1
    ))
    return styles


def build_pdf_response(filename, title, table_data, col_widths=None, extra_note=None):
    """
    Generic PDF builder: takes a title and a table (list of lists),
    returns an HttpResponse with the PDF attached.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = get_styles()
    elements = []

    elements.append(Paragraph(title, styles['ReportTitle']))
    elements.append(Spacer(1, 12))

    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f2f2')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    if extra_note:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(extra_note, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer