"""Citation model: a single citation extracted from a document."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import CitationType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.validation import Validation


class Citation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "citations"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    citation_type: Mapped[CitationType] = mapped_column(
        SAEnum(CitationType, name="citation_type"),
        default=CitationType.UNKNOWN,
        nullable=False,
    )

    # Raw matched text and its location in the source document.
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Parsed case metadata ----------------------------------------------
    case_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reporter: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pin_cite: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    court: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # --- Parsed statute / regulation metadata ------------------------------
    title_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)  # USC / CFR
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="citations")
    validation: Mapped["Validation | None"] = relationship(
        back_populates="citation",
        cascade="all, delete-orphan",
        uselist=False,
    )
