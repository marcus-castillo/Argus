"""Reference corpus models: reporters registry and known sources."""
from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.db import Base
from app.models.enums import SourceType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Reporter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A legal reporter (e.g. ``U.S.``, ``F.3d``) with its valid ranges."""

    __tablename__ = "reporters"

    abbreviation: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    # Inclusive published volume range (max_volume null = open-ended/active).
    min_volume: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Inclusive year range the reporter was/is in print.
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Courts whose opinions appear in this reporter (comma-separated keys).
    courts: Mapped[str] = mapped_column(String(512), nullable=False, default="")


class ReferenceSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A known, ground-truth legal source used to verify citations."""

    __tablename__ = "reference_sources"
    __table_args__ = (
        UniqueConstraint(
            "volume", "reporter", "page", name="uq_reference_case_locator"
        ),
    )

    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type"), nullable=False, index=True
    )

    # Human-readable identity.
    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

    # --- Case locator ------------------------------------------------------
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    reporter: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    court: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # --- Statute / regulation locator --------------------------------------
    title_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    section: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Free text used to build the embedding (case name + summary).
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )
