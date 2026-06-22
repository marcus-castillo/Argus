"""Framework-free data structures consumed by the report builders."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ReportCitation:
    raw_text: str
    citation_type: str
    result: str
    confidence: float
    summary: str
    matched_source: str | None
    findings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReportData:
    document_id: str
    filename: str
    generated_at: datetime
    total_citations: int
    verified: int
    suspicious: int
    hallucinated: int
    unverifiable: int
    verification_rate: float
    average_confidence: float
    citations: list[ReportCitation] = field(default_factory=list)
