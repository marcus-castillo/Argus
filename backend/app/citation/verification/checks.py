"""Individual verification checks.

Each check is a pure function ``(ParsedCitation, VerificationContext) -> Finding``
(or ``None`` when not applicable). Checks never raise on bad data; they encode
problems as failed findings so the engine can aggregate them.
"""
from __future__ import annotations

from datetime import datetime

from app.citation.sources.base import VerificationContext
from app.citation.types import Finding, ParsedCitation
from app.enums import FindingSeverity as Sev

# A page can't plausibly exceed this in any single reporter volume.
_MAX_PAGE = 4000
_CURRENT_YEAR = datetime.now().year


def _ok(check: str, message: str, severity: Sev = Sev.INFO) -> Finding:
    return Finding(check=check, passed=True, severity=severity, message=message)


def _fail(check: str, message: str, severity: Sev) -> Finding:
    return Finding(check=check, passed=False, severity=severity, message=message)


# --------------------------------------------------------------------------- #
# Case checks
# --------------------------------------------------------------------------- #
def check_existence(p: ParsedCitation, ctx: VerificationContext) -> Finding:
    if ctx.exact_match is not None:
        return _ok(
            "existence",
            f"Exact match found: “{ctx.exact_match.title}”.",
        )
    if ctx.candidates:
        top = ctx.candidates[0]
        if top.score >= 0.92:
            # The case exists by name, but the cited volume/reporter/page does
            # not resolve to it — i.e. the locator is wrong. Suspicious, not
            # outright fabricated.
            return _fail(
                "existence",
                (
                    f"Case “{top.title}” exists, but no source sits at the cited "
                    "volume/reporter/page; the locator appears incorrect."
                ),
                Sev.ERROR,
            )
        return _fail(
            "existence",
            (
                "No exact source found at this locator; closest match is "
                f"“{top.title}” (score {top.score:.2f})."
            ),
            Sev.WARNING,
        )
    return _fail(
        "existence",
        "No source exists at this reporter/volume/page. Possible fabrication.",
        Sev.CRITICAL,
    )


def check_reporter(p: ParsedCitation, ctx: VerificationContext) -> Finding:
    if not p.reporter:
        return _fail("reporter", "Citation has no reporter.", Sev.ERROR)
    if ctx.reporter_known and ctx.reporter is not None:
        return _ok("reporter", f"Reporter “{p.reporter}” is a recognized reporter.")
    return _fail(
        "reporter",
        f"Reporter “{p.reporter}” is not a recognized legal reporter.",
        Sev.CRITICAL,
    )


def check_volume(p: ParsedCitation, ctx: VerificationContext) -> Finding | None:
    if p.volume is None:
        return None
    if p.volume <= 0:
        return _fail("volume", f"Volume {p.volume} is not positive.", Sev.ERROR)
    if ctx.reporter is None:
        return None  # can't range-check an unknown reporter
    if ctx.reporter.volume_in_range(p.volume):
        return _ok("volume", f"Volume {p.volume} is within published range.")
    hi = ctx.reporter.max_volume
    return _fail(
        "volume",
        (
            f"Volume {p.volume} is outside the published range "
            f"({ctx.reporter.min_volume}–{hi if hi is not None else 'current'}) "
            f"for {p.reporter}."
        ),
        Sev.ERROR,
    )


def check_page(p: ParsedCitation, ctx: VerificationContext) -> Finding | None:
    if p.page is None:
        return None
    if p.page <= 0:
        return _fail("page", f"Page {p.page} is not positive.", Sev.ERROR)
    if p.page > _MAX_PAGE:
        return _fail(
            "page",
            f"Page {p.page} is implausibly large for a single volume.",
            Sev.WARNING,
        )
    return _ok("page", f"Page {p.page} is plausible.")


def check_year(p: ParsedCitation, ctx: VerificationContext) -> Finding | None:
    if p.year is None:
        return None
    if p.year > _CURRENT_YEAR:
        return _fail(
            "year",
            f"Year {p.year} is in the future.",
            Sev.CRITICAL,
        )
    if p.year < 1754:  # earliest US-relevant reported decisions
        return _fail("year", f"Year {p.year} predates US case reporting.", Sev.ERROR)
    # Temporal consistency with the reporter's active span.
    if ctx.reporter is not None and not ctx.reporter.year_in_range(p.year):
        return _fail(
            "year",
            (
                f"Year {p.year} falls outside the years {p.reporter} was in "
                f"print ({ctx.reporter.start_year}–"
                f"{ctx.reporter.end_year or 'present'})."
            ),
            Sev.ERROR,
        )
    # Consistency with the matched source's known decision year.
    src = ctx.exact_match or (ctx.candidates[0] if ctx.candidates else None)
    if src is not None and src.year is not None and src.year != p.year:
        return _fail(
            "year",
            (
                f"Cited year {p.year} does not match the source's decision year "
                f"{src.year}."
            ),
            Sev.ERROR,
        )
    return _ok("year", f"Year {p.year} is consistent.")


def check_court(p: ParsedCitation, ctx: VerificationContext) -> Finding | None:
    src = ctx.exact_match
    if src is None or not src.court or not p.court:
        return None
    if _court_matches(p.court, src.court):
        return _ok("court", f"Court “{p.court}” matches the source.")
    return _fail(
        "court",
        f"Cited court “{p.court}” conflicts with the source court “{src.court}”.",
        Sev.WARNING,
    )


def _court_matches(a: str, b: str) -> bool:
    na, nb = a.lower().replace(".", "").strip(), b.lower().replace(".", "").strip()
    return na in nb or nb in na


def check_case_format(p: ParsedCitation, ctx: VerificationContext) -> Finding | None:
    raw = (p.normalized_text or p.raw_text or "")
    problems: list[str] = []
    if p.volume is None or p.reporter is None or p.page is None:
        problems.append("missing volume/reporter/page component")
    if p.case_name and " v. " not in p.case_name and " v " not in p.case_name:
        problems.append("party separator “v.” is malformed")
    if "  " in raw:
        problems.append("irregular spacing")
    if problems:
        return _fail(
            "format",
            "Formatting anomaly: " + "; ".join(problems) + ".",
            Sev.WARNING,
        )
    return _ok("format", "Citation is well-formed (Bluebook-shaped).")


# --------------------------------------------------------------------------- #
# Statute / regulation checks
# --------------------------------------------------------------------------- #
def check_code_existence(p: ParsedCitation, ctx: VerificationContext) -> Finding:
    if ctx.exact_match is not None:
        return _ok("existence", f"Provision found: “{ctx.exact_match.title}”.")
    if ctx.candidates:
        top = ctx.candidates[0]
        return _fail(
            "existence",
            (
                f"No exact provision at {p.title_number} {p.code} § {p.section}; "
                f"closest is “{top.title}”."
            ),
            Sev.WARNING,
        )
    return _fail(
        "existence",
        (
            f"No such provision: {p.title_number} {p.code} § {p.section}. "
            "Possible fabrication."
        ),
        Sev.CRITICAL,
    )


def check_code_format(p: ParsedCitation, ctx: VerificationContext) -> Finding:
    problems: list[str] = []
    if p.title_number is None or p.title_number <= 0:
        problems.append("missing or invalid title number")
    if not p.code:
        problems.append("missing code (U.S.C./C.F.R.)")
    if not p.section:
        problems.append("missing section")
    # U.S.C. has 54 positive-law titles; C.F.R. has 50.
    if p.code == "U.S.C." and p.title_number and p.title_number > 54:
        problems.append(f"U.S.C. has no Title {p.title_number}")
    if p.code == "C.F.R." and p.title_number and p.title_number > 50:
        problems.append(f"C.F.R. has no Title {p.title_number}")
    if problems:
        sev = Sev.ERROR if any("no Title" in x for x in problems) else Sev.WARNING
        return _fail("format", "Formatting issue: " + "; ".join(problems) + ".", sev)
    return _ok("format", "Statutory/regulatory format is well-formed.")
