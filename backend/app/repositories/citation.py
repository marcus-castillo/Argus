"""Citation repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.citation import Citation
from app.models.validation import Validation
from app.repositories.base import BaseRepository


class CitationRepository(BaseRepository[Citation]):
    model = Citation

    async def list_for_document(
        self, document_id: uuid.UUID
    ) -> list[Citation]:
        stmt = (
            select(Citation)
            .where(Citation.document_id == document_id)
            .order_by(Citation.start_offset)
            .options(
                selectinload(Citation.validation).selectinload(Validation.findings),
                selectinload(Citation.validation).selectinload(
                    Validation.matched_source
                ),
            )
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
