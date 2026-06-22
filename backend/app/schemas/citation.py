"""Citation DTOs."""
from __future__ import annotations

import uuid

from app.models.enums import CitationType
from app.schemas.base import ORMModel
from app.schemas.validation import ValidationRead


class CitationRead(ORMModel):
    id: uuid.UUID
    citation_type: CitationType
    raw_text: str
    normalized_text: str | None = None
    start_offset: int
    end_offset: int

    case_name: str | None = None
    volume: int | None = None
    reporter: str | None = None
    page: int | None = None
    pin_cite: int | None = None
    year: int | None = None
    court: str | None = None

    title_number: int | None = None
    code: str | None = None
    section: str | None = None

    validation: ValidationRead | None = None
