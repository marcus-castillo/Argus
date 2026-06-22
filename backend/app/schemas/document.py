"""Document DTOs."""
from __future__ import annotations

import uuid
from datetime import datetime

from app.models.enums import DocumentStatus
from app.schemas.base import ORMModel
from app.schemas.citation import CitationRead


class DocumentRead(ORMModel):
    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    page_count: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentRead):
    citations: list[CitationRead] = []


class DocumentList(ORMModel):
    items: list[DocumentRead]
    total: int
