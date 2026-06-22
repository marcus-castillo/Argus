"""DB-backed implementation of the domain :class:`SourceProvider`."""
from __future__ import annotations

from app.citation.embeddings import embed
from app.citation.sources.base import (
    ReporterInfo,
    SourceProvider,
    VerificationContext,
)
from app.citation.types import ParsedCitation, SourceRecord
from app.core.config import settings
from app.models.enums import CitationType, SourceType
from app.models.reference import ReferenceSource, Reporter
from app.repositories.reference import ReferenceRepository


def _to_record(src: ReferenceSource, score: float = 1.0) -> SourceRecord:
    return SourceRecord(
        id=str(src.id),
        source_type=src.source_type,
        title=src.title,
        volume=src.volume,
        reporter=src.reporter,
        page=src.page,
        year=src.year,
        court=src.court,
        title_number=src.title_number,
        code=src.code,
        section=src.section,
        score=score,
    )


def _to_reporter_info(rep: Reporter) -> ReporterInfo:
    courts = [c.strip() for c in (rep.courts or "").split(",") if c.strip()]
    return ReporterInfo(
        abbreviation=rep.abbreviation,
        name=rep.name,
        min_volume=rep.min_volume,
        max_volume=rep.max_volume,
        start_year=rep.start_year,
        end_year=rep.end_year,
        courts=courts,
    )


def _name_similarity(a: str, b: str) -> float:
    """Token-set Jaccard similarity between two case names (0..1)."""
    ta = {t for t in a.lower().replace(".", "").replace(",", "").split() if t}
    tb = {t for t in b.lower().replace(".", "").replace(",", "").split() if t}
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union


class CorpusSourceProvider(SourceProvider):
    """Resolves lookups against the seeded reference corpus."""

    def __init__(self, references: ReferenceRepository) -> None:
        self._refs = references

    async def build_context(self, parsed: ParsedCitation) -> VerificationContext:
        if parsed.citation_type == CitationType.CASE:
            return await self._case_context(parsed)
        return await self._provision_context(parsed)

    # ------------------------------------------------------------------ #
    async def _case_context(self, p: ParsedCitation) -> VerificationContext:
        ctx = VerificationContext()

        # Reporter registry lookup.
        if p.reporter:
            rep = await self._refs.get_reporter(p.reporter)
            if rep is not None:
                ctx.reporter = _to_reporter_info(rep)
                ctx.reporter_known = True

        # Exact locator match.
        if p.volume is not None and p.reporter and p.page is not None:
            exact = await self._refs.find_case_by_locator(
                p.volume, p.reporter, p.page
            )
            if exact is not None:
                ctx.exact_match = _to_record(exact, score=1.0)

        # Fuzzy candidates by name + semantics (used when locator misses).
        candidates: dict[str, SourceRecord] = {}
        if p.case_name:
            for src in await self._refs.find_case_by_name(p.case_name):
                sim = _name_similarity(p.case_name, src.title)
                candidates[str(src.id)] = _to_record(src, score=sim)

        query_text = p.case_name or p.normalized_text or p.raw_text
        emb = embed(query_text)
        for src, sim in await self._refs.semantic_search(emb, SourceType.CASE):
            rid = str(src.id)
            name_sim = (
                _name_similarity(p.case_name, src.title) if p.case_name else 0.0
            )
            score = max(sim, name_sim)
            if rid in candidates:
                candidates[rid].score = max(candidates[rid].score, score)
            else:
                candidates[rid] = _to_record(src, score=score)

        ctx.candidates = sorted(
            candidates.values(), key=lambda r: r.score, reverse=True
        )
        return ctx

    async def _provision_context(self, p: ParsedCitation) -> VerificationContext:
        ctx = VerificationContext()
        source_type = (
            SourceType.STATUTE
            if p.citation_type == CitationType.STATUTE
            else SourceType.REGULATION
        )
        if p.title_number is not None and p.code and p.section:
            exact = await self._refs.find_provision(
                source_type, p.title_number, p.code, p.section
            )
            if exact is not None:
                ctx.exact_match = _to_record(exact, score=1.0)

        emb = embed(p.normalized_text or p.raw_text)
        ctx.candidates = [
            _to_record(src, score=sim)
            for src, sim in await self._refs.semantic_search(emb, source_type)
            if sim >= settings.semantic_match_threshold - 0.2
        ]
        return ctx
