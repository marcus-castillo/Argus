"""Idempotent database seeding.

Run with:  python -m seed.seed

Loads the reporter registry and reference corpus (computing embeddings), then
creates a demo document and runs it through the verification pipeline inline so
the dashboard is populated on first boot.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import func, select

from app.citation.embeddings import embed
from app.core.db import SessionFactory
from app.core.logging import get_logger
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.reference import ReferenceSource, Reporter
from app.services.processing_service import ProcessingService
from app.services.storage import FileStorage
from seed import corpus

logger = get_logger("seed")

SAMPLE = Path(__file__).parent / "samples" / "demo_brief.txt"
DEMO_FILENAME = "demo_brief.txt"


async def _seed_reporters(session) -> int:
    existing = await session.scalar(select(func.count()).select_from(Reporter))
    if existing:
        logger.info("Reporters already seeded (%d); skipping.", existing)
        return 0
    for abbr, name, minv, maxv, sy, ey, courts in corpus.REPORTERS:
        session.add(
            Reporter(
                abbreviation=abbr,
                name=name,
                min_volume=minv,
                max_volume=maxv,
                start_year=sy,
                end_year=ey,
                courts=courts,
            )
        )
    await session.flush()
    return len(corpus.REPORTERS)


async def _seed_sources(session) -> int:
    existing = await session.scalar(
        select(func.count()).select_from(ReferenceSource)
    )
    if existing:
        logger.info("Reference sources already seeded (%d); skipping.", existing)
        return 0
    rows = corpus.all_sources()
    for row in rows:
        session.add(
            ReferenceSource(embedding=embed(row["searchable_text"]), **row)
        )
    await session.flush()
    return len(rows)


async def _seed_demo_document(session) -> bool:
    existing = await session.scalar(
        select(Document).where(Document.filename == DEMO_FILENAME)
    )
    if existing is not None:
        logger.info("Demo document already exists; skipping.")
        return False

    data = SAMPLE.read_bytes()
    storage = FileStorage()
    path = storage.save(DEMO_FILENAME, data)
    doc = Document(
        filename=DEMO_FILENAME,
        content_type="text/plain",
        size_bytes=len(data),
        storage_path=path,
        status=DocumentStatus.QUEUED,
    )
    session.add(doc)
    await session.flush()

    # Process inline so the demo dashboard is populated immediately.
    processing = ProcessingService(session, storage=storage)
    count = await processing.process_document(doc.id)
    logger.info("Demo document processed: %d citations", count)
    return True


async def run() -> None:
    async with SessionFactory() as session:
        n_rep = await _seed_reporters(session)
        n_src = await _seed_sources(session)
        await _seed_demo_document(session)
        await session.commit()
    logger.info("Seed complete (%d reporters, %d sources).", n_rep, n_src)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
