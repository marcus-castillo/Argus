"""Unit tests for report builders."""
import csv
import io
import json
from datetime import datetime, timezone

import pytest

from app.reports import (
    ReportCitation,
    ReportData,
    build_csv_report,
    build_json_report,
    build_pdf_report,
)

pytestmark = pytest.mark.unit


def sample_data() -> ReportData:
    return ReportData(
        document_id="doc-1",
        filename="brief.txt",
        generated_at=datetime(2026, 6, 22, tzinfo=timezone.utc),
        total_citations=2,
        verified=1,
        suspicious=1,
        hallucinated=0,
        unverifiable=0,
        verification_rate=0.5,
        average_confidence=0.75,
        citations=[
            ReportCitation(
                raw_text="Brown v. Board of Education, 347 U.S. 483 (1954)",
                citation_type="case",
                result="verified",
                confidence=1.0,
                summary="Verified.",
                matched_source="Brown v. Board of Education",
                findings=["Exact match found."],
            ),
            ReportCitation(
                raw_text="Roe v. Wade, 410 U.S. 113 (1971)",
                citation_type="case",
                result="suspicious",
                confidence=0.55,
                summary="Year mismatch.",
                matched_source="Roe v. Wade",
                findings=["Cited year 1971 does not match 1973."],
            ),
        ],
    )


def test_json_report_roundtrips():
    payload = json.loads(build_json_report(sample_data()))
    assert payload["summary"]["total_citations"] == 2
    assert payload["summary"]["verified"] == 1
    assert len(payload["citations"]) == 2
    assert payload["citations"][0]["result"] == "verified"


def test_csv_report_has_header_and_rows():
    raw = build_csv_report(sample_data()).decode("utf-8")
    rows = list(csv.reader(io.StringIO(raw)))
    assert rows[0] == [
        "citation", "type", "result", "confidence",
        "matched_source", "summary", "findings",
    ]
    assert len(rows) == 3  # header + 2
    assert rows[1][2] == "verified"


def test_pdf_report_is_valid_pdf():
    data = build_pdf_report(sample_data())
    assert data[:5] == b"%PDF-"
    assert len(data) > 1000
