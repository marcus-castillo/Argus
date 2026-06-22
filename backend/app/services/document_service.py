"""Use-cases for uploading and reading documents."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.job import ProcessingJob
from app.repositories.document import DocumentRepository
from app.repositories.job import JobRepository
from app.services.storage import FileStorage
from app.services.text_extraction import SUPPORTED_EXTENSIONS


class DocumentService:
    def __init__(self, session: AsyncSession, storage: FileStorage | None = None):
        self.session = session
        self.documents = DocumentRepository(session)
        self.jobs = JobRepository(session)
        self.storage = storage or FileStorage()

    async def upload(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
        owner_id: uuid.UUID | None = None,
    ) -> Document:
        if not data:
            raise ValidationError("Uploaded file is empty.")
        if len(data) > settings.max_upload_bytes:
            raise ValidationError(
                f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)} MiB limit."
            )
        ext = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported extension “{ext}”. Allowed: "
                + ", ".join(sorted(SUPPORTED_EXTENSIONS))
            )

        storage_path = self.storage.save(filename, data)
        doc = Document(
            owner_id=owner_id,
            filename=filename,
            content_type=content_type or "application/octet-stream",
            size_bytes=len(data),
            storage_path=storage_path,
            status=DocumentStatus.QUEUED,
        )
        await self.documents.add(doc)

        # Enqueue background processing.
        await self.jobs.add(
            ProcessingJob(
                job_type="process_document",
                document_id=doc.id,
                max_attempts=settings.job_max_attempts,
            )
        )
        return doc

    async def list(self, limit: int = 100, offset: int = 0) -> list[Document]:
        return await self.documents.list(limit=limit, offset=offset)

    async def get(self, document_id: uuid.UUID) -> Document:
        doc = await self.documents.get(document_id)
        if doc is None:
            raise NotFoundError(f"Document {document_id} not found.")
        return doc

    async def get_with_citations(self, document_id: uuid.UUID) -> Document:
        doc = await self.documents.get_with_citations(document_id)
        if doc is None:
            raise NotFoundError(f"Document {document_id} not found.")
        return doc
