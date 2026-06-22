"""Dashboard DTO."""
from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.models.enums import DocumentStatus


class DashboardStats(BaseModel):
    document_id: uuid.UUID
    status: DocumentStatus
    total_citations: int
    verified: int
    suspicious: int
    hallucinated: int
    unverifiable: int
    flagged: int
    verification_rate: float
    average_confidence: float
