"""Pluggable verification data sources.

The verification engine never talks to a database directly. Instead a
:class:`SourceProvider` resolves lookups into plain :class:`SourceRecord` and
:class:`ReporterInfo` values. The default implementation
(:class:`app.services.source_provider.CorpusSourceProvider`) is backed by the
seeded ``reference_sources`` table; swap it for a Westlaw / CourtListener
implementation in production.
"""
from app.citation.sources.base import (
    ReporterInfo,
    SourceProvider,
    VerificationContext,
)

__all__ = ["ReporterInfo", "SourceProvider", "VerificationContext"]
