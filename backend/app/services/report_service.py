"""Assemble report data from persisted entities and render it."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.enums import ValidationResult
from app.reports import (
    ReportCitation,
    ReportData,
    build_csv_report,
    build_json_report,
    build_pdf_report,
)
from app.repositories.document import DocumentRepository
from app.repositories.validation import ValidationRepository


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.validations = ValidationRepository(session)

    async def build_data(self, document_id: uuid.UUID) -> ReportData:
        doc = await self.documents.get_with_citations(document_id)
        if doc is None:
            raise NotFoundError(f"Document {document_id} not found.")

        counts = await self.validations.result_counts(document_id)
        avg_conf = await self.validations.average_confidence(document_id)
        total = sum(counts.values())
        verified = counts.get(ValidationResult.VERIFIED.value, 0)

        report_citations: list[ReportCitation] = []
        for cit in doc.citations:
            v = cit.validation
            matched = None
            if v and v.matched_source:
                matched = v.matched_source.title
            report_citations.append(
                ReportCitation(
                    raw_text=cit.raw_text,
                    citation_type=cit.citation_type.value,
                    result=v.result.value if v else "unverifiable",
                    confidence=v.confidence if v else 0.0,
                    summary=v.summary if v else "Not yet validated.",
                    matched_source=matched,
                    findings=[f.message for f in v.findings] if v else [],
                )
            )

        return ReportData(
            document_id=str(doc.id),
            filename=doc.filename,
            generated_at=datetime.now(timezone.utc),
            total_citations=total,
            verified=verified,
            suspicious=counts.get(ValidationResult.SUSPICIOUS.value, 0),
            hallucinated=counts.get(ValidationResult.HALLUCINATED.value, 0),
            unverifiable=counts.get(ValidationResult.UNVERIFIABLE.value, 0),
            verification_rate=round(verified / total, 4) if total else 0.0,
            average_confidence=round(avg_conf, 4),
            citations=report_citations,
        )

    async def as_json(self, document_id: uuid.UUID) -> bytes:
        return build_json_report(await self.build_data(document_id))

    async def as_csv(self, document_id: uuid.UUID) -> bytes:
        return build_csv_report(await self.build_data(document_id))

    async def as_pdf(self, document_id: uuid.UUID) -> bytes:
        return build_pdf_report(await self.build_data(document_id))
