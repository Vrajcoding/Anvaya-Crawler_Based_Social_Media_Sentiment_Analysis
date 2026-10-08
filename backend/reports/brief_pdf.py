"""
reports/brief_pdf.py
Generates a 1-page PDF Incident Brief (EN/GU) from an Incident object.
"""

import os
from datetime import datetime
from typing import Dict, Any, List
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a font that supports Gujarati if possible. 
# For this prototype, we'll rely on a standard font and hope for OS fallback, 
# or use standard Helvetica for English and transliterated Gujarati.
# To do this perfectly in production, we'd bundle a font like NotoSansGujarati.ttf.

def generate_incident_pdf(incident: Dict[str, Any], evidence_posts: List[Dict[str, Any]]) -> BytesIO:
    """
    Generate a PDF brief for an incident.
    Returns a BytesIO buffer containing the PDF data.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
        title=f"Incident Report: {incident.get('id')}"
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'IncidentTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12
    )
    
    heading2 = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8,
        spaceBefore=16
    )

    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.leading = 14

    elements = []

    # Title
    elements.append(Paragraph(f"SentinelAI Incident Brief", title_style))
    elements.append(Paragraph(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", normal_style))
    elements.append(Spacer(1, 15))

    # Summary Table (Meta info)
    severity_color = '#ef4444' if incident.get("severity_label") == 'CRITICAL' else '#f97316'
    
    meta_data = [
        ['Incident ID:', incident.get('id', 'Unknown')],
        ['Severity:', incident.get('severity_label', 'Unknown')],
        ['Location (District):', incident.get('district', 'Unknown')],
        ['Time Window:', f"{incident.get('first_seen', '')[:16]} to {incident.get('last_seen', '')[:16]}"],
        ['Platforms Affected:', ", ".join(incident.get('platforms', []))],
        ['Total Posts Involved:', str(incident.get('post_count', 0))]
    ]
    
    t = Table(meta_data, colWidths=[120, 380])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor(severity_color)),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Narrative Summary
    elements.append(Paragraph("Narrative Summary", heading2))
    elements.append(Paragraph(incident.get("narrative", "No narrative available."), normal_style))
    elements.append(Spacer(1, 20))

    # Evidence Posts
    elements.append(Paragraph("Top Evidence Posts", heading2))
    
    for i, post in enumerate(evidence_posts[:5]):
        author = post.get("author_username", "Unknown")
        platform = post.get("platform", "Unknown").upper()
        ts = post.get("crawled_at", "")[:16]
        content = post.get("content", "")
        
        post_header = f"<b>{i+1}. @{author}</b> on {platform} at {ts}"
        elements.append(Paragraph(post_header, normal_style))
        
        # Indent content slightly
        content_style = ParagraphStyle(
            'EvidenceContent',
            parent=normal_style,
            leftIndent=20,
            textColor=colors.HexColor('#475569'),
            spaceBefore=4,
            spaceAfter=12
        )
        elements.append(Paragraph(f'"{content}"', content_style))

    # Recommended Action Placeholder
    elements.append(Paragraph("Recommended Actions", heading2))
    actions = [
        "1. Issue takedown request to involved platforms for the top evidence posts.",
        "2. Dispatch clarification/counter-message via local PR channels.",
        "3. Alert station house officer (SHO) for the affected district."
    ]
    for action in actions:
        elements.append(Paragraph(action, normal_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
