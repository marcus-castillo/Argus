"""Validation models: the verification result for a citation and its findings."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import FindingSeverity, ValidationResult
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.citation import Citation
    from app.models.reference import ReferenceSource


class Validation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "validations"

    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    result: Mapped[ValidationResult] = mapped_column(
        SAEnum(ValidationResult, name="validation_result"),
        nullable=False,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Best-matching supporting source, if any (the "source linking" requirement).
    matched_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reference_sources.id", ondelete="SET NULL"),
        nullable=True,
    )

    citation: Mapped["Citation"] = relationship(back_populates="validation")
    matched_source: Mapped["ReferenceSource | None"] = relationship()
    findings: Mapped[list["ValidationFinding"]] = relationship(
        back_populates="validation",
        cascade="all, delete-orphan",
        order_by="ValidationFinding.created_at",
    )


class ValidationFinding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "validation_findings"

    validation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The check that produced this finding, e.g. "reporter", "year", "existence".
    check: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(
        SAEnum(FindingSeverity, name="finding_severity"),
        nullable=False,
    )
    passed: Mapped[bool] = mapped_column(nullable=False, default=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    validation: Mapped["Validation"] = relationship(back_populates="findings")
