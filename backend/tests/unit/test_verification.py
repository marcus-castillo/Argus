"""Unit tests for the verification engine (pure, no DB)."""
import pytest

from app.citation.sources.base import ReporterInfo, VerificationContext
from app.citation.types import ParsedCitation, SourceRecord
from app.citation.verification import verify
from app.models.enums import CitationType, SourceType, ValidationResult

pytestmark = pytest.mark.unit

US_REPORTER = ReporterInfo(
    abbreviation="U.S.",
    name="United States Reports",
    min_volume=1,
    max_volume=700,
    start_year=1790,
    end_year=None,
    courts=["scotus"],
)


def case(**kw) -> ParsedCitation:
    base = dict(
        citation_type=CitationType.CASE,
        raw_text="X v. Y, 347 U.S. 483 (1954)",
        start_offset=0,
        end_offset=10,
        case_name="Brown v. Board of Education",
        volume=347,
        reporter="U.S.",
        page=483,
        year=1954,
    )
    base.update(kw)
    return ParsedCitation(**base)


def source(**kw) -> SourceRecord:
    base = dict(
        id="11111111-1111-1111-1111-111111111111",
        source_type=SourceType.CASE,
        title="Brown v. Board of Education",
        volume=347,
        reporter="U.S.",
        page=483,
        year=1954,
        court="scotus",
        score=1.0,
    )
    base.update(kw)
    return SourceRecord(**base)


def test_exact_match_is_verified():
    ctx = VerificationContext(
        exact_match=source(), reporter=US_REPORTER, reporter_known=True
    )
    out = verify(case(), ctx)
    assert out.result == ValidationResult.VERIFIED
    assert out.confidence == 1.0
    assert out.matched_source_id == source().id


def test_unknown_reporter_is_hallucinated():
    p = case(reporter="Z.3d")
    ctx = VerificationContext(reporter=None, reporter_known=False)
    out = verify(p, ctx)
    assert out.result == ValidationResult.HALLUCINATED
    reporter_finding = next(f for f in out.findings if f.check == "reporter")
    assert not reporter_finding.passed


def test_future_year_is_hallucinated():
    p = case(year=2099)
    ctx = VerificationContext(reporter=US_REPORTER, reporter_known=True)
    out = verify(p, ctx)
    assert out.result == ValidationResult.HALLUCINATED
    year_finding = next(f for f in out.findings if f.check == "year")
    assert not year_finding.passed


def test_no_source_is_hallucinated():
    p = case(volume=999, page=9999)
    ctx = VerificationContext(reporter=US_REPORTER, reporter_known=True)
    out = verify(p, ctx)
    assert out.result == ValidationResult.HALLUCINATED


def test_wrong_year_with_matching_source_is_suspicious():
    # Source says 1954, citation says 1955 -> exists but inconsistent.
    p = case(year=1955)
    ctx = VerificationContext(
        exact_match=source(year=1954), reporter=US_REPORTER, reporter_known=True
    )
    out = verify(p, ctx)
    assert out.result == ValidationResult.SUSPICIOUS
    year_finding = next(f for f in out.findings if f.check == "year")
    assert not year_finding.passed


def test_name_match_but_wrong_locator_is_suspicious():
    # Case exists by name (strong candidate), but locator resolves to nothing.
    p = case(page=999)
    ctx = VerificationContext(
        candidates=[source(page=483, score=1.0)],
        reporter=US_REPORTER,
        reporter_known=True,
    )
    out = verify(p, ctx)
    assert out.result == ValidationResult.SUSPICIOUS


def test_volume_out_of_range_flags_error():
    p = case(volume=5000)
    ctx = VerificationContext(reporter=US_REPORTER, reporter_known=True)
    out = verify(p, ctx)
    vol_finding = next(f for f in out.findings if f.check == "volume")
    assert not vol_finding.passed


def test_statute_exact_match_verified():
    p = ParsedCitation(
        citation_type=CitationType.STATUTE,
        raw_text="42 U.S.C. § 1983",
        start_offset=0,
        end_offset=16,
        title_number=42,
        code="U.S.C.",
        section="1983",
    )
    src = SourceRecord(
        id="22222222-2222-2222-2222-222222222222",
        source_type=SourceType.STATUTE,
        title="42 U.S.C. § 1983",
        title_number=42,
        code="U.S.C.",
        section="1983",
    )
    out = verify(p, VerificationContext(exact_match=src))
    assert out.result == ValidationResult.VERIFIED


def test_impossible_statute_title_is_hallucinated():
    p = ParsedCitation(
        citation_type=CitationType.STATUTE,
        raw_text="99 U.S.C. § 9999",
        start_offset=0,
        end_offset=16,
        title_number=99,
        code="U.S.C.",
        section="9999",
    )
    out = verify(p, VerificationContext())
    assert out.result == ValidationResult.HALLUCINATED


def test_confidence_drops_with_severity():
    clean = verify(
        case(),
        VerificationContext(
            exact_match=source(), reporter=US_REPORTER, reporter_known=True
        ),
    )
    broken = verify(
        case(year=2099),
        VerificationContext(reporter=US_REPORTER, reporter_known=True),
    )
    assert clean.confidence > broken.confidence
