"""Health / readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep

router = APIRouter()


@router.get("/health", summary="Liveness and DB readiness probe")
async def health(session: SessionDep) -> dict[str, str]:
    db_ok = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - exercised only when DB is down
        db_ok = "unavailable"
    return {"status": "ok", "database": db_ok}
