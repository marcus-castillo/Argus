"""Dashboard aggregation use-case."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.enums import ValidationResult
from app.repositories.document import DocumentRepository
from app.repositories.validation import ValidationRepository
from app.schemas.dashboard import DashboardStats


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.validations = ValidationRepository(session)

    async def for_document(self, document_id: uuid.UUID) -> DashboardStats:
        doc = await self.documents.get(document_id)
        if doc is None:
            raise NotFoundError(f"Document {document_id} not found.")

        counts = await self.validations.result_counts(document_id)
        avg_conf = await self.validations.average_confidence(document_id)

        verified = counts.get(ValidationResult.VERIFIED.value, 0)
        suspicious = counts.get(ValidationResult.SUSPICIOUS.value, 0)
        hallucinated = counts.get(ValidationResult.HALLUCINATED.value, 0)
        unverifiable = counts.get(ValidationResult.UNVERIFIABLE.value, 0)
        total = verified + suspicious + hallucinated + unverifiable

        verification_rate = (verified / total) if total else 0.0
        flagged = suspicious + hallucinated

        return DashboardStats(
            document_id=document_id,
            status=doc.status,
            total_citations=total,
            verified=verified,
            suspicious=suspicious,
            hallucinated=hallucinated,
            unverifiable=unverifiable,
            flagged=flagged,
            verification_rate=round(verification_rate, 4),
            average_confidence=round(avg_conf, 4),
        )
