"""Reference corpus repository: locator + semantic lookups, reporter registry."""
from __future__ import annotations

from sqlalchemy import func, select

from app.models.enums import SourceType
from app.models.reference import ReferenceSource, Reporter
from app.repositories.base import BaseRepository


class ReferenceRepository(BaseRepository[ReferenceSource]):
    model = ReferenceSource

    # --- Reporter registry -------------------------------------------------
    async def get_reporter(self, abbreviation: str) -> Reporter | None:
        stmt = select(Reporter).where(Reporter.abbreviation == abbreviation)
        return await self.session.scalar(stmt)

    async def all_reporters(self) -> list[Reporter]:
        result = await self.session.scalars(select(Reporter))
        return list(result.all())

    # --- Case locator ------------------------------------------------------
    async def find_case_by_locator(
        self, volume: int, reporter: str, page: int
    ) -> ReferenceSource | None:
        stmt = select(ReferenceSource).where(
            ReferenceSource.source_type == SourceType.CASE,
            ReferenceSource.volume == volume,
            ReferenceSource.reporter == reporter,
            ReferenceSource.page == page,
        )
        return await self.session.scalar(stmt)

    # --- Statute / regulation locator -------------------------------------
    async def find_provision(
        self, source_type: SourceType, title_number: int, code: str, section: str
    ) -> ReferenceSource | None:
        stmt = select(ReferenceSource).where(
            ReferenceSource.source_type == source_type,
            ReferenceSource.title_number == title_number,
            ReferenceSource.code == code,
            ReferenceSource.section == section,
        )
        return await self.session.scalar(stmt)

    # --- Semantic search (pgvector) ---------------------------------------
    async def semantic_search(
        self,
        embedding: list[float],
        source_type: SourceType,
        limit: int = 5,
    ) -> list[tuple[ReferenceSource, float]]:
        """Return ``(source, similarity)`` ordered by cosine similarity desc.

        Uses pgvector's cosine distance operator ``<=>``; similarity = 1 - dist.
        """
        distance = ReferenceSource.embedding.cosine_distance(embedding)
        stmt = (
            select(ReferenceSource, distance.label("distance"))
            .where(
                ReferenceSource.source_type == source_type,
                ReferenceSource.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(limit)
        )
        rows = await self.session.execute(stmt)
        return [(row[0], 1.0 - float(row[1])) for row in rows.all()]

    async def find_case_by_name(
        self, name: str, limit: int = 5
    ) -> list[ReferenceSource]:
        """Trigram-ish name search using ILIKE on the title."""
        pattern = f"%{name.strip()}%"
        stmt = (
            select(ReferenceSource)
            .where(
                ReferenceSource.source_type == SourceType.CASE,
                func.lower(ReferenceSource.title).like(func.lower(pattern)),
            )
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
