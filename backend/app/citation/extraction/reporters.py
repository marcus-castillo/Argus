"""Canonical reporter abbreviations used by the extractor regex.

This is the *lexical* set (what strings can appear as a reporter token). The
authoritative validity ranges live in the ``reporters`` table; this list only
needs to be permissive enough to capture candidates for verification.
"""
from __future__ import annotations

# Order matters: longer / more specific abbreviations first so the alternation
# is greedy in the right direction (e.g. "F. Supp. 2d" before "F.").
KNOWN_REPORTERS: list[str] = [
    "U.S.",
    "S. Ct.",
    "L. Ed. 2d",
    "L. Ed.",
    "F.4th",
    "F.3d",
    "F.2d",
    "F. Supp. 3d",
    "F. Supp. 2d",
    "F. Supp.",
    "F.",
    "F. App'x",
    "A.3d",
    "A.2d",
    "A.",
    "N.E.3d",
    "N.E.2d",
    "N.E.",
    "N.W.2d",
    "N.W.",
    "P.3d",
    "P.2d",
    "P.",
    "S.E.2d",
    "S.E.",
    "S.W.3d",
    "S.W.2d",
    "S.W.",
    "So. 3d",
    "So. 2d",
    "So.",
    "Cal. Rptr. 3d",
    "Cal. Rptr. 2d",
    "Cal. Rptr.",
    "N.Y.S.3d",
    "N.Y.S.2d",
]


def reporter_alternation() -> str:
    """Return a regex alternation matching any known reporter abbreviation."""
    import re

    # Sort by length desc so longer abbreviations win in the alternation.
    ordered = sorted(set(KNOWN_REPORTERS), key=len, reverse=True)
    return "|".join(re.escape(r) for r in ordered)
