"""Serialize :class:`ReportData` into PDF, CSV, and JSON bytes."""
from __future__ import annotations

import csv
import io
import json

from app.reports.model import ReportData


def build_json_report(data: ReportData) -> bytes:
    payload = {
        "document_id": data.document_id,
        "filename": data.filename,
        "generated_at": data.generated_at.isoformat(),
        "summary": {
            "total_citations": data.total_citations,
            "verified": data.verified,
            "suspicious": data.suspicious,
            "hallucinated": data.hallucinated,
            "unverifiable": data.unverifiable,
            "verification_rate": data.verification_rate,
            "average_confidence": data.average_confidence,
        },
        "citations": [
            {
                "raw_text": c.raw_text,
                "citation_type": c.citation_type,
                "result": c.result,
                "confidence": c.confidence,
                "summary": c.summary,
                "matched_source": c.matched_source,
                "findings": c.findings,
            }
            for c in data.citations
        ],
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def build_csv_report(data: ReportData) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "citation",
            "type",
            "result",
            "confidence",
            "matched_source",
            "summary",
            "findings",
        ]
    )
    for c in data.citations:
        writer.writerow(
            [
                c.raw_text,
                c.citation_type,
                c.result,
                f"{c.confidence:.4f}",
                c.matched_source or "",
                c.summary,
                " | ".join(c.findings),
            ]
        )
    return buffer.getvalue().encode("utf-8")


def build_pdf_report(data: ReportData) -> bytes:
    """Render a PDF report with reportlab (platypus)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        title=f"CiteCheck Report — {data.filename}",
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=10)
    elements: list = []

    elements.append(Paragraph("CiteCheck Verification Report", styles["Title"]))
    elements.append(Paragraph(f"Document: {data.filename}", styles["Normal"]))
    elements.append(
        Paragraph(
            f"Generated: {data.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.2 * inch))

    summary_table = Table(
        [
            ["Total", "Verified", "Suspicious", "Hallucinated", "Verif. rate"],
            [
                str(data.total_citations),
                str(data.verified),
                str(data.suspicious),
                str(data.hallucinated),
                f"{data.verification_rate * 100:.1f}%",
            ],
        ],
        colWidths=[1.2 * inch] * 5,
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Citations", styles["Heading2"]))

    result_color = {
        "verified": colors.HexColor("#dcfce7"),
        "suspicious": colors.HexColor("#fef9c3"),
        "hallucinated": colors.HexColor("#fee2e2"),
        "unverifiable": colors.HexColor("#e2e8f0"),
    }

    rows: list[list] = [["Citation", "Result", "Conf.", "Notes"]]
    style_cmds: list = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, c in enumerate(data.citations, start=1):
        notes = c.summary
        if c.matched_source:
            notes += f"\nSource: {c.matched_source}"
        rows.append(
            [
                Paragraph(c.raw_text, small),
                c.result,
                f"{c.confidence:.2f}",
                Paragraph(notes, small),
            ]
        )
        style_cmds.append(
            ("BACKGROUND", (1, i), (1, i), result_color.get(c.result, colors.white))
        )

    table = Table(rows, colWidths=[2.6 * inch, 1.0 * inch, 0.6 * inch, 2.8 * inch])
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
