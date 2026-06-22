"""Document upload, listing, citations, dashboard, and report endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.api.deps import (
    DashboardServiceDep,
    DocumentServiceDep,
    ReportServiceDep,
)
from app.schemas.citation import CitationRead
from app.schemas.dashboard import DashboardStats
from app.schemas.document import DocumentDetail, DocumentList, DocumentRead

router = APIRouter()


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a brief/motion/memo and queue it for verification",
)
async def upload_document(
    service: DocumentServiceDep,
    file: UploadFile = File(...),
) -> DocumentRead:
    data = await file.read()
    doc = await service.upload(
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return DocumentRead.model_validate(doc)


@router.get("", response_model=DocumentList, summary="List uploaded documents")
async def list_documents(
    service: DocumentServiceDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> DocumentList:
    docs = await service.list(limit=limit, offset=offset)
    total = await service.documents.count()
    return DocumentList(
        items=[DocumentRead.model_validate(d) for d in docs], total=total
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetail,
    summary="Get a document with its citations and validations",
)
async def get_document(
    document_id: uuid.UUID,
    service: DocumentServiceDep,
) -> DocumentDetail:
    doc = await service.get_with_citations(document_id)
    return DocumentDetail.model_validate(doc)


@router.get(
    "/{document_id}/citations",
    response_model=list[CitationRead],
    summary="List a document's citations with verification results",
)
async def get_citations(
    document_id: uuid.UUID,
    service: DocumentServiceDep,
) -> list[CitationRead]:
    doc = await service.get_with_citations(document_id)
    return [CitationRead.model_validate(c) for c in doc.citations]


@router.get(
    "/{document_id}/dashboard",
    response_model=DashboardStats,
    summary="Aggregated verification stats for a document",
)
async def get_dashboard(
    document_id: uuid.UUID,
    service: DashboardServiceDep,
) -> DashboardStats:
    return await service.for_document(document_id)


@router.get(
    "/{document_id}/report.json",
    summary="Download the verification report as JSON",
)
async def report_json(
    document_id: uuid.UUID,
    service: ReportServiceDep,
) -> Response:
    body = await service.as_json(document_id)
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="citecheck-{document_id}.json"'
        },
    )


@router.get(
    "/{document_id}/report.csv",
    summary="Download the verification report as CSV",
)
async def report_csv(
    document_id: uuid.UUID,
    service: ReportServiceDep,
) -> Response:
    body = await service.as_csv(document_id)
    return Response(
        content=body,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="citecheck-{document_id}.csv"'
        },
    )


@router.get(
    "/{document_id}/report.pdf",
    summary="Download the verification report as PDF",
)
async def report_pdf(
    document_id: uuid.UUID,
    service: ReportServiceDep,
) -> Response:
    body = await service.as_pdf(document_id)
    return Response(
        content=body,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="citecheck-{document_id}.pdf"'
        },
    )
