"""Validation repository, including dashboard aggregation."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.citation import Citation
from app.models.enums import ValidationResult
from app.models.validation import Validation
from app.repositories.base import BaseRepository


class ValidationRepository(BaseRepository[Validation]):
    model = Validation

    async def result_counts(self, document_id: uuid.UUID) -> dict[str, int]:
        """Return counts of validations per result for one document."""
        stmt = (
            select(Validation.result, func.count())
            .join(Citation, Citation.id == Validation.citation_id)
            .where(Citation.document_id == document_id)
            .group_by(Validation.result)
        )
        rows = await self.session.execute(stmt)
        counts = {r.value: 0 for r in ValidationResult}
        for result, n in rows.all():
            key = result.value if hasattr(result, "value") else str(result)
            counts[key] = int(n)
        return counts

    async def average_confidence(self, document_id: uuid.UUID) -> float:
        stmt = (
            select(func.avg(Validation.confidence))
            .join(Citation, Citation.id == Validation.citation_id)
            .where(Citation.document_id == document_id)
        )
        return float(await self.session.scalar(stmt) or 0.0)
