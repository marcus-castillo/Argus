"""FastAPI dependency providers wiring sessions into services."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.services.dashboard_service import DashboardService
from app.services.document_service import DocumentService
from app.services.report_service import ReportService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_document_service(session: SessionDep) -> DocumentService:
    return DocumentService(session)


def get_dashboard_service(session: SessionDep) -> DashboardService:
    return DashboardService(session)


def get_report_service(session: SessionDep) -> ReportService:
    return ReportService(session)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
