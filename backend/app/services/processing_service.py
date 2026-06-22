"""The core pipeline: parse a document, extract citations, verify, persist.

Invoked by the background worker for each ``process_document`` job. Wrapped in
a single transaction per document by the caller.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.citation.extraction import extract_citations
from app.citation.types import ParsedCitation, VerificationOutcome
from app.citation.verification import verify
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.models.citation import Citation
from app.models.enums import DocumentStatus
from app.models.validation import Validation, ValidationFinding
from app.repositories.citation import CitationRepository
from app.repositories.document import DocumentRepository
from app.repositories.reference import ReferenceRepository
from app.services.source_provider import CorpusSourceProvider
from app.services.storage import FileStorage
from app.services.text_extraction import extract_text

logger = get_logger(__name__)


class ProcessingService:
    def __init__(self, session: AsyncSession, storage: FileStorage | None = None):
        self.session = session
        self.documents = DocumentRepository(session)
        self.citations = CitationRepository(session)
        self.provider = CorpusSourceProvider(ReferenceRepository(session))
        self.storage = storage or FileStorage()

    async def process_document(self, document_id: uuid.UUID) -> int:
        """Run the full pipeline for one document. Returns citation count."""
        doc = await self.documents.get(document_id)
        if doc is None:
            raise NotFoundError(f"Document {document_id} not found.")

        doc.status = DocumentStatus.PROCESSING
        await self.session.flush()

        # 1) Extract text from the stored file.
        data = self.storage.read(doc.storage_path)
        extracted = extract_text(doc.filename, doc.content_type, data)
        doc.extracted_text = extracted.text
        doc.page_count = extracted.page_count

        # 2) Extract citation candidates.
        parsed_list = extract_citations(extracted.text)
        logger.info(
            "Document %s: extracted %d citation(s)", document_id, len(parsed_list)
        )

        # 3) Verify each and persist.
        for parsed in parsed_list:
            citation = self._persist_citation(doc.id, parsed)
            await self.citations.add(citation)
            ctx = await self.provider.build_context(parsed)
            outcome = verify(parsed, ctx)
            await self._persist_validation(citation.id, outcome)

        doc.status = DocumentStatus.COMPLETED
        doc.error_message = None
        await self.session.flush()
        return len(parsed_list)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _persist_citation(document_id: uuid.UUID, p: ParsedCitation) -> Citation:
        return Citation(
            document_id=document_id,
            citation_type=p.citation_type,
            raw_text=p.raw_text,
            normalized_text=p.normalized_text,
            start_offset=p.start_offset,
            end_offset=p.end_offset,
            case_name=p.case_name,
            volume=p.volume,
            reporter=p.reporter,
            page=p.page,
            pin_cite=p.pin_cite,
            year=p.year,
            court=p.court,
            title_number=p.title_number,
            code=p.code,
            section=p.section,
        )

    async def _persist_validation(
        self, citation_id: uuid.UUID, outcome: VerificationOutcome
    ) -> None:
        matched_source_id = (
            uuid.UUID(outcome.matched_source_id)
            if outcome.matched_source_id
            else None
        )
        validation = Validation(
            citation_id=citation_id,
            result=outcome.result,
            confidence=outcome.confidence,
            summary=outcome.summary,
            matched_source_id=matched_source_id,
        )
        self.session.add(validation)
        await self.session.flush()
        for f in outcome.findings:
            self.session.add(
                ValidationFinding(
                    validation_id=validation.id,
                    check=f.check,
                    severity=f.severity,
                    passed=f.passed,
                    message=f.message,
                )
            )
        await self.session.flush()
