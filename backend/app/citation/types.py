"""Framework-free domain types for the citation engine."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.enums import (
    CitationType,
    FindingSeverity,
    SourceType,
    ValidationResult,
)


@dataclass(slots=True)
class ParsedCitation:
    """A citation extracted from text, with parsed metadata.

    Fields are ``None`` when not applicable to the citation type or when the
    extractor could not parse them.
    """

    citation_type: CitationType
    raw_text: str
    start_offset: int
    end_offset: int
    normalized_text: str | None = None

    # Case fields
    case_name: str | None = None
    volume: int | None = None
    reporter: str | None = None
    page: int | None = None
    pin_cite: int | None = None
    year: int | None = None
    court: str | None = None

    # Statute / regulation fields
    title_number: int | None = None
    code: str | None = None
    section: str | None = None


@dataclass(slots=True)
class SourceRecord:
    """A ground-truth source returned by a :class:`SourceProvider`."""

    id: str
    source_type: SourceType
    title: str
    volume: int | None = None
    reporter: str | None = None
    page: int | None = None
    year: int | None = None
    court: str | None = None
    title_number: int | None = None
    code: str | None = None
    section: str | None = None
    score: float = 1.0  # match score (1.0 == exact locator match)


@dataclass(slots=True)
class Finding:
    """The outcome of a single verification check."""

    check: str
    passed: bool
    severity: FindingSeverity
    message: str


@dataclass(slots=True)
class VerificationOutcome:
    """Aggregate verification result for one citation."""

    result: ValidationResult
    confidence: float
    summary: str
    findings: list[Finding] = field(default_factory=list)
    matched_source_id: str | None = None
