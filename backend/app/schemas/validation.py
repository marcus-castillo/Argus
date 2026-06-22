"""Validation + finding DTOs."""
from __future__ import annotations

import uuid

from pydantic import Field

from app.models.enums import FindingSeverity, SourceType, ValidationResult
from app.schemas.base import ORMModel


class FindingRead(ORMModel):
    check: str
    severity: FindingSeverity
    passed: bool
    message: str


class MatchedSourceRead(ORMModel):
    id: uuid.UUID
    source_type: SourceType
    title: str
    volume: int | None = None
    reporter: str | None = None
    page: int | None = None
    year: int | None = None
    court: str | None = None
    code: str | None = None
    section: str | None = None


class ValidationRead(ORMModel):
    id: uuid.UUID
    result: ValidationResult
    confidence: float
    summary: str
    findings: list[FindingRead] = Field(default_factory=list)
    matched_source: MatchedSourceRead | None = None
