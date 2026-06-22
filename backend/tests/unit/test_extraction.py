"""Unit tests for the citation extractor."""
import pytest

from app.citation.extraction import extract_citations
from app.models.enums import CitationType

pytestmark = pytest.mark.unit


def _by_type(cites, t):
    return [c for c in cites if c.citation_type == t]


def test_extracts_named_case_with_full_metadata():
    text = "As held in Brown v. Board of Education, 347 U.S. 483, 495 (1954)."
    cites = extract_citations(text)
    cases = _by_type(cites, CitationType.CASE)
    assert len(cases) == 1
    c = cases[0]
    assert c.case_name == "Brown v. Board of Education"
    assert c.volume == 347
    assert c.reporter == "U.S."
    assert c.page == 483
    assert c.pin_cite == 495
    assert c.year == 1954


def test_extracts_roe_v_wade():
    cites = extract_citations("See Roe v. Wade, 410 U.S. 113 (1973).")
    c = _by_type(cites, CitationType.CASE)[0]
    assert c.volume == 410 and c.reporter == "U.S." and c.page == 113
    assert c.year == 1973


def test_extracts_statute_with_section_symbol():
    cites = extract_citations("brought under 42 U.S.C. § 1983 for damages")
    statutes = _by_type(cites, CitationType.STATUTE)
    assert len(statutes) == 1
    s = statutes[0]
    assert s.title_number == 42
    assert s.code == "U.S.C."
    assert s.section == "1983"


def test_extracts_statute_without_section_symbol():
    cites = extract_citations("28 U.S.C. 1331 confers jurisdiction")
    s = _by_type(cites, CitationType.STATUTE)[0]
    assert s.title_number == 28 and s.section == "1331"


def test_extracts_regulation():
    cites = extract_citations("see 29 C.F.R. § 1604.11 (harassment)")
    regs = _by_type(cites, CitationType.REGULATION)
    assert len(regs) == 1
    r = regs[0]
    assert r.title_number == 29 and r.code == "C.F.R." and r.section == "1604.11"


def test_extracts_federal_reporter_with_court_and_year():
    cites = extract_citations("Smith v. Jones, 812 F.3d 447 (9th Cir. 2016)")
    c = _by_type(cites, CitationType.CASE)[0]
    assert c.reporter == "F.3d" and c.volume == 812 and c.page == 447
    assert c.year == 2016
    assert c.court and "Cir" in c.court


def test_offsets_point_to_source_text():
    text = "xx Roe v. Wade, 410 U.S. 113 (1973) yy"
    c = extract_citations(text)[0]
    assert text[c.start_offset : c.end_offset].startswith("Roe v. Wade")


def test_multiple_citations_sorted_by_offset():
    text = "First 42 U.S.C. § 1983 then Roe v. Wade, 410 U.S. 113 (1973)."
    cites = extract_citations(text)
    offsets = [c.start_offset for c in cites]
    assert offsets == sorted(offsets)


def test_empty_text_returns_nothing():
    assert extract_citations("") == []
