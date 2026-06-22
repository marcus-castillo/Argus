"""Verification engine: runs checks and aggregates an outcome + confidence.

Confidence model
----------------
Start at 1.0 and subtract a penalty per failed finding, weighted by severity.
The *result* classification is then derived from the strongest failure and
whether a supporting source was found:

* no failures + source found            -> VERIFIED
* source found + only warnings/errors    -> SUSPICIOUS
* critical failure / no source           -> HALLUCINATED
* citation could not be parsed at all     -> UNVERIFIABLE
"""
from __future__ import annotations

from app.citation.sources.base import VerificationContext
from app.citation.types import Finding, ParsedCitation, VerificationOutcome
from app.citation.verification import checks
from app.enums import CitationType
from app.enums import FindingSeverity as Sev
from app.enums import ValidationResult

_SEVERITY_PENALTY: dict[Sev, float] = {
    Sev.INFO: 0.0,
    Sev.WARNING: 0.18,
    Sev.ERROR: 0.45,
    Sev.CRITICAL: 0.85,
}

_CASE_CHECKS = (
    checks.check_existence,
    checks.check_reporter,
    checks.check_volume,
    checks.check_page,
    checks.check_year,
    checks.check_court,
    checks.check_case_format,
)

_CODE_CHECKS = (
    checks.check_code_existence,
    checks.check_code_format,
)


class VerificationEngine:
    """Stateless aggregator over the individual checks."""

    def verify(
        self, parsed: ParsedCitation, ctx: VerificationContext
    ) -> VerificationOutcome:
        if parsed.citation_type == CitationType.CASE:
            check_fns = _CASE_CHECKS
        elif parsed.citation_type in (
            CitationType.STATUTE,
            CitationType.REGULATION,
        ):
            check_fns = _CODE_CHECKS
        else:
            return VerificationOutcome(
                result=ValidationResult.UNVERIFIABLE,
                confidence=0.0,
                summary="Citation type could not be determined.",
                findings=[],
            )

        findings: list[Finding] = []
        for fn in check_fns:
            f = fn(parsed, ctx)
            if f is not None:
                findings.append(f)

        return self._aggregate(parsed, ctx, findings)

    # ------------------------------------------------------------------ #
    def _aggregate(
        self,
        parsed: ParsedCitation,
        ctx: VerificationContext,
        findings: list[Finding],
    ) -> VerificationOutcome:
        confidence = 1.0
        worst = Sev.INFO
        severity_order = [Sev.INFO, Sev.WARNING, Sev.ERROR, Sev.CRITICAL]
        for f in findings:
            if not f.passed:
                confidence -= _SEVERITY_PENALTY[f.severity]
                if severity_order.index(f.severity) > severity_order.index(worst):
                    worst = f.severity
        confidence = max(0.0, min(1.0, confidence))

        has_source = ctx.exact_match is not None or any(
            c.score >= 0.92 for c in ctx.candidates
        )
        any_failure = any(not f.passed for f in findings)

        if not any_failure and has_source:
            result = ValidationResult.VERIFIED
        elif worst == Sev.CRITICAL or not has_source:
            result = ValidationResult.HALLUCINATED
        else:
            result = ValidationResult.SUSPICIOUS

        matched_id = ctx.exact_match.id if ctx.exact_match else (
            ctx.candidates[0].id if ctx.candidates and ctx.candidates[0].score >= 0.92
            else None
        )

        return VerificationOutcome(
            result=result,
            confidence=round(confidence, 4),
            summary=self._summarize(result, findings),
            findings=findings,
            matched_source_id=matched_id,
        )

    @staticmethod
    def _summarize(result: ValidationResult, findings: list[Finding]) -> str:
        failed = [f for f in findings if not f.passed]
        if result == ValidationResult.VERIFIED:
            return "Citation verified against a known source with consistent metadata."
        if not failed:
            return result.value
        lead = {
            ValidationResult.HALLUCINATED: "Likely hallucinated",
            ValidationResult.SUSPICIOUS: "Metadata inconsistencies detected",
            ValidationResult.UNVERIFIABLE: "Could not verify",
        }.get(result, "Issues detected")
        return f"{lead}: " + " ".join(f.message for f in failed[:3])


_DEFAULT_ENGINE = VerificationEngine()


def verify(parsed: ParsedCitation, ctx: VerificationContext) -> VerificationOutcome:
    """Convenience wrapper using a shared engine instance."""
    return _DEFAULT_ENGINE.verify(parsed, ctx)
