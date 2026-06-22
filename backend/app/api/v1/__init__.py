"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.v1 import documents, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

__all__ = ["api_router"]
