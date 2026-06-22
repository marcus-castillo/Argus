"""Abstract source provider and the context consumed by the engine."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.citation.types import ParsedCitation, SourceRecord


@dataclass(slots=True)
class ReporterInfo:
    """Validity metadata for a reporter abbreviation."""

    abbreviation: str
    name: str
    min_volume: int
    max_volume: int | None
    start_year: int
    end_year: int | None
    courts: list[str] = field(default_factory=list)

    def volume_in_range(self, volume: int) -> bool:
        if volume < self.min_volume:
            return False
        if self.max_volume is not None and volume > self.max_volume:
            return False
        return True

    def year_in_range(self, year: int) -> bool:
        if year < self.start_year:
            return False
        if self.end_year is not None and year > self.end_year:
            return False
        return True


@dataclass(slots=True)
class VerificationContext:
    """Everything the engine needs to verify one citation, pre-fetched.

    Building this is the provider's job (I/O); consuming it is the engine's job
    (pure logic). This split keeps the engine synchronous and unit-testable.
    """

    # Exact locator hit (volume+reporter+page, or code+section) if one exists.
    exact_match: SourceRecord | None = None
    # Ranked fuzzy candidates (case-name / semantic matches).
    candidates: list[SourceRecord] = field(default_factory=list)
    # Reporter validity record for the cited reporter, if the abbreviation
    # is known to the registry at all.
    reporter: ReporterInfo | None = None
    # Whether the reporter abbreviation appears in the registry.
    reporter_known: bool = False


class SourceProvider(ABC):
    """Resolves citation lookups into framework-free records."""

    @abstractmethod
    async def build_context(self, parsed: ParsedCitation) -> VerificationContext:
        """Fetch everything needed to verify ``parsed``."""
        raise NotImplementedError
