"""Regex-driven extraction of case, statutory, and regulatory citations.

The extractor is intentionally permissive: it captures *candidates* and parses
whatever metadata it can. Validity judgements are the verification engine's job,
not the extractor's. Each match records character offsets so the UI can
highlight the citation in the source text.
"""
from __future__ import annotations

import re

from app.citation.extraction.reporters import reporter_alternation
from app.citation.types import ParsedCitation
from app.enums import CitationType

_REPORTER = reporter_alternation()

# A party name: a capitalized token followed by further capitalized tokens or
# lowercase legal particles (of/and/the/...). Excluding arbitrary lowercase
# words stops the match from swallowing preceding sentence text like
# "...the Supreme Court held in Brown v. ...".
_PARTY = (
    r"[A-Z][A-Za-z'.\-]*"
    r"(?:\s+(?:[A-Z][A-Za-z'.\-]*|of|and|the|for|ex|rel\.?|&)){0,6}?"
)

# --- Case citations --------------------------------------------------------
# e.g. "Brown v. Board of Education, 347 U.S. 483, 495 (1954)"
#       <----- case name ----->  vol  rptr  pg   pin    year
_CASE_RE = re.compile(
    r"""
    (?P<case_name>
        %(party)s        # plaintiff
        \s+v\.?\s+
        %(party)s        # defendant
    )
    ,\s*
    (?P<volume>\d{1,4})\s+
    (?P<reporter>%(reporter)s)\s+
    (?P<page>\d{1,5})
    (?:\s*,\s*(?P<pin>\d{1,5}))?                            # optional pin cite
    (?:\s*\(\s*(?P<court>[A-Za-z0-9.\s]+?\s+)?(?P<year>\d{4})\s*\))?  # (Court Year)
    """
    % {"reporter": _REPORTER, "party": _PARTY},
    re.VERBOSE,
)

# A named case whose reporter token is NOT in the known set, e.g.
# "Hampton v. Sterling Industries, 999 Z.3d 1234 (2050)". Capturing these is
# essential for flagging fabricated/unknown reporters during verification.
_GENERIC_CASE_RE = re.compile(
    r"""
    (?P<case_name>
        %(party)s
        \s+v\.?\s+
        %(party)s
    )
    ,\s*
    (?P<volume>\d{1,4})\s+
    (?P<reporter>[A-Z][A-Za-z.]*(?:\s+[A-Za-z.]+){0,3}?(?:\s?\d+[a-z]{0,2})?)\s+
    (?P<page>\d{1,5})
    (?:\s*,\s*(?P<pin>\d{1,5}))?
    (?:\s*\(\s*(?P<court>[A-Za-z0-9.\s]+?\s+)?(?P<year>\d{4})\s*\))?
    """
    % {"party": _PARTY},
    re.VERBOSE,
)

# A "bare" reporter citation with no case name, e.g. "347 U.S. 483 (1954)".
_BARE_CASE_RE = re.compile(
    r"""
    (?<![A-Za-z0-9])
    (?P<volume>\d{1,4})\s+
    (?P<reporter>%(reporter)s)\s+
    (?P<page>\d{1,5})
    (?:\s*,\s*(?P<pin>\d{1,5}))?
    (?:\s*\(\s*(?P<court>[A-Za-z0-9.\s]+?\s+)?(?P<year>\d{4})\s*\))?
    """
    % {"reporter": _REPORTER},
    re.VERBOSE,
)

# --- Statutory citations ---------------------------------------------------
# e.g. "42 U.S.C. § 1983" or "42 U.S.C. 1983" or "5 U.S.C. §§ 551-559"
_STATUTE_RE = re.compile(
    r"""
    (?<![A-Za-z0-9])
    (?P<title>\d{1,3})\s+
    (?P<code>U\.?S\.?C\.?(?:A\.?)?)\s*
    (?:§{1,2}\s*)?
    (?P<section>\d+[A-Za-z]?(?:[-–]\d+)?(?:\([A-Za-z0-9]+\))*)
    """,
    re.VERBOSE,
)

# --- Regulatory citations --------------------------------------------------
# e.g. "29 C.F.R. § 1604.11" or "40 C.F.R. 261.3"
_REGULATION_RE = re.compile(
    r"""
    (?<![A-Za-z0-9])
    (?P<title>\d{1,3})\s+
    (?P<code>C\.?F\.?R\.?)\s*
    (?:§{1,2}\s*)?
    (?P<section>\d+(?:\.\d+)?(?:\([A-Za-z0-9]+\))*)
    """,
    re.VERBOSE,
)


# Leading Bluebook signal words that are not part of the case name itself.
_SIGNAL_WORDS = {
    "see", "accord", "cf", "compare", "contra", "but", "also", "e.g", "eg",
    "id", "viz",
}


def _strip_signal_prefix(name: str) -> str:
    tokens = name.split()
    i = 0
    while i < len(tokens) - 1 and tokens[i].lower().strip(".,") in _SIGNAL_WORDS:
        i += 1
    return " ".join(tokens[i:])


def _norm_case(m: re.Match[str]) -> ParsedCitation:
    gd = m.groupdict()
    court = (gd.get("court") or "").strip() or None
    name = gd.get("case_name")
    if name:
        name = _strip_signal_prefix(re.sub(r"\s+", " ", name).strip())
    else:
        name = None
    return ParsedCitation(
        citation_type=CitationType.CASE,
        raw_text=m.group(0).strip(),
        start_offset=m.start(),
        end_offset=m.end(),
        normalized_text=_normalize_whitespace(m.group(0)),
        case_name=name,
        volume=int(gd["volume"]),
        reporter=_normalize_whitespace(gd["reporter"]),
        page=int(gd["page"]),
        pin_cite=int(gd["pin"]) if gd.get("pin") else None,
        year=int(gd["year"]) if gd.get("year") else None,
        court=court,
    )


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


class CitationExtractor:
    """Stateless extractor. Call :meth:`extract` with document text."""

    def extract(self, text: str) -> list[ParsedCitation]:
        if not text:
            return []
        results: list[ParsedCitation] = []
        claimed: list[tuple[int, int]] = []  # spans already taken by a case cite

        # 1) Case citations with a case name (highest precedence).
        for m in _CASE_RE.finditer(text):
            results.append(_norm_case(m))
            claimed.append((m.start(), m.end()))

        # 2) Named cases with an unknown/fabricated reporter token.
        for m in _GENERIC_CASE_RE.finditer(text):
            if _overlaps(m.start(), m.end(), claimed):
                continue
            results.append(_norm_case(m))
            claimed.append((m.start(), m.end()))

        # 3) Bare reporter citations not already inside a named case cite.
        for m in _BARE_CASE_RE.finditer(text):
            if _overlaps(m.start(), m.end(), claimed):
                continue
            results.append(_norm_case(m))
            claimed.append((m.start(), m.end()))

        # 3) Statutes.
        for m in _STATUTE_RE.finditer(text):
            gd = m.groupdict()
            results.append(
                ParsedCitation(
                    citation_type=CitationType.STATUTE,
                    raw_text=m.group(0).strip(),
                    start_offset=m.start(),
                    end_offset=m.end(),
                    normalized_text=_normalize_whitespace(m.group(0)),
                    title_number=int(gd["title"]),
                    code=_normalize_code(gd["code"]),
                    section=gd["section"],
                )
            )

        # 4) Regulations.
        for m in _REGULATION_RE.finditer(text):
            gd = m.groupdict()
            results.append(
                ParsedCitation(
                    citation_type=CitationType.REGULATION,
                    raw_text=m.group(0).strip(),
                    start_offset=m.start(),
                    end_offset=m.end(),
                    normalized_text=_normalize_whitespace(m.group(0)),
                    title_number=int(gd["title"]),
                    code=_normalize_code(gd["code"]),
                    section=gd["section"],
                )
            )

        results.sort(key=lambda c: c.start_offset)
        return results


def _normalize_code(code: str) -> str:
    """Normalize ``USC`` / ``U.S.C.A`` / ``CFR`` to canonical dotted forms."""
    compact = code.replace(".", "").replace(" ", "").upper()
    if compact.startswith("USC"):
        return "U.S.C.A." if compact.endswith("A") else "U.S.C."
    if compact.startswith("CFR"):
        return "C.F.R."
    return code


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(not (end <= s or start >= e) for s, e in spans)


def extract_citations(text: str) -> list[ParsedCitation]:
    """Convenience function using a default extractor."""
    return CitationExtractor().extract(text)
