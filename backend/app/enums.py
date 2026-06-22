"""Dependency-free enumerations shared by the domain, ORM, and schemas.

Kept at the top level (not under ``app.models``) so the pure citation engine can
import them without pulling in SQLAlchemy.
"""
from __future__ import annotations

import enum


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CitationType(str, enum.Enum):
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"
    UNKNOWN = "unknown"


class SourceType(str, enum.Enum):
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"


class ValidationResult(str, enum.Enum):
    """Overall outcome of verifying a single citation."""

    VERIFIED = "verified"          # exists + metadata consistent
    SUSPICIOUS = "suspicious"      # exists but metadata inconsistent
    HALLUCINATED = "hallucinated"  # no plausible source / impossible
    UNVERIFIABLE = "unverifiable"  # could not be checked (e.g. parse failure)


class FindingSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
