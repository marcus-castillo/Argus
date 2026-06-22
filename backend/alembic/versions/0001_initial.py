"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-22
"""
from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    document_status = postgresql.ENUM(
        "uploaded", "queued", "processing", "completed", "failed",
        name="document_status",
    )
    citation_type = postgresql.ENUM(
        "case", "statute", "regulation", "unknown", name="citation_type"
    )
    source_type = postgresql.ENUM(
        "case", "statute", "regulation", name="source_type"
    )
    validation_result = postgresql.ENUM(
        "verified", "suspicious", "hallucinated", "unverifiable",
        name="validation_result",
    )
    finding_severity = postgresql.ENUM(
        "info", "warning", "error", "critical", name="finding_severity"
    )
    job_status = postgresql.ENUM(
        "pending", "running", "succeeded", "failed", name="job_status"
    )
    for enum in (
        document_status,
        citation_type,
        source_type,
        validation_result,
        finding_severity,
        job_status,
    ):
        enum.create(op.get_bind(), checkfirst=True)

    ts = lambda: sa.Column(  # noqa: E731
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # --- reporters ---------------------------------------------------------
    op.create_table(
        "reporters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("abbreviation", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("min_volume", sa.Integer, nullable=False, server_default="1"),
        sa.Column("max_volume", sa.Integer, nullable=True),
        sa.Column("start_year", sa.Integer, nullable=False),
        sa.Column("end_year", sa.Integer, nullable=True),
        sa.Column("courts", sa.String(512), nullable=False, server_default=""),
        ts(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_reporters_abbreviation", "reporters", ["abbreviation"])

    # --- reference_sources -------------------------------------------------
    op.create_table(
        "reference_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("volume", sa.Integer, nullable=True),
        sa.Column("reporter", sa.String(64), nullable=True),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("court", sa.String(128), nullable=True),
        sa.Column("title_number", sa.Integer, nullable=True),
        sa.Column("code", sa.String(64), nullable=True),
        sa.Column("section", sa.String(64), nullable=True),
        sa.Column("searchable_text", sa.Text, nullable=False, server_default=""),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        ts(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.UniqueConstraint(
            "volume", "reporter", "page", name="uq_reference_case_locator"
        ),
    )
    op.create_index("ix_reference_sources_source_type", "reference_sources", ["source_type"])
    op.create_index("ix_reference_sources_title", "reference_sources", ["title"])
    op.create_index("ix_reference_sources_reporter", "reference_sources", ["reporter"])
    op.create_index("ix_reference_sources_volume", "reference_sources", ["volume"])
    op.create_index("ix_reference_sources_page", "reference_sources", ["page"])
    op.create_index("ix_reference_sources_code", "reference_sources", ["code"])
    op.create_index("ix_reference_sources_section", "reference_sources", ["section"])
    # IVFFlat index for cosine similarity search.
    op.execute(
        "CREATE INDEX ix_reference_sources_embedding ON reference_sources "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )

    # --- documents ---------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("status", document_status, nullable=False, server_default="uploaded"),
        sa.Column("extracted_text", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        ts(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_index("ix_documents_status", "documents", ["status"])

    # --- citations ---------------------------------------------------------
    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("citation_type", citation_type, nullable=False, server_default="unknown"),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("normalized_text", sa.Text, nullable=True),
        sa.Column("start_offset", sa.Integer, nullable=False),
        sa.Column("end_offset", sa.Integer, nullable=False),
        sa.Column("case_name", sa.String(512), nullable=True),
        sa.Column("volume", sa.Integer, nullable=True),
        sa.Column("reporter", sa.String(64), nullable=True),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("pin_cite", sa.Integer, nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("court", sa.String(128), nullable=True),
        sa.Column("title_number", sa.Integer, nullable=True),
        sa.Column("code", sa.String(64), nullable=True),
        sa.Column("section", sa.String(64), nullable=True),
        ts(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_citations_document_id", "citations", ["document_id"])

    # --- validations -------------------------------------------------------
    op.create_table(
        "validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "citation_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("citations.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),
        sa.Column("result", validation_result, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("summary", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "matched_source_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reference_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        ts(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_validations_citation_id", "validations", ["citation_id"])
    op.create_index("ix_validations_result", "validations", ["result"])

    # --- validation_findings ----------------------------------------------
    op.create_table(
        "validation_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "validation_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("validations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("check", sa.String(64), nullable=False),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("message", sa.Text, nullable=False),
        ts(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index(
        "ix_validation_findings_validation_id",
        "validation_findings",
        ["validation_id"],
    )

    # --- processing_jobs ---------------------------------------------------
    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(64), nullable=False, server_default="process_document"),
        sa.Column(
            "document_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("status", job_status, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        ts(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_processing_jobs_document_id", "processing_jobs", ["document_id"])
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("validation_findings")
    op.drop_table("validations")
    op.drop_table("citations")
    op.drop_table("documents")
    op.drop_index("ix_reference_sources_embedding", table_name="reference_sources")
    op.drop_table("reference_sources")
    op.drop_table("reporters")
    for name in (
        "document_status",
        "citation_type",
        "source_type",
        "validation_result",
        "finding_severity",
        "job_status",
    ):
        op.execute(f"DROP TYPE IF EXISTS {name}")
