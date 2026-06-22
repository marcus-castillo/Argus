"""Document repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.citation import Citation
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.validation import Validation
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    async def get_with_citations(self, document_id: uuid.UUID) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.citations)
                .selectinload(Citation.validation)
                .selectinload(Validation.findings),
                selectinload(Document.citations)
                .selectinload(Citation.validation)
                .selectinload(Validation.matched_source),
            )
        )
        return await self.session.scalar(stmt)

    async def set_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        *,
        error_message: str | None = None,
    ) -> None:
        doc = await self.get(document_id)
        if doc is None:
            return
        doc.status = status
        if error_message is not None:
            doc.error_message = error_message
