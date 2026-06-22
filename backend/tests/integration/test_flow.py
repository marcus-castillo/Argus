"""End-to-end backend integration: upload -> process -> dashboard -> report.

Requires a Postgres database with pgvector (the CI ``postgres`` service).
"""
import uuid
from pathlib import Path

import pytest

from app.citation.embeddings import embed
from app.models.reference import ReferenceSource, Reporter
from app.services.processing_service import ProcessingService
from seed import corpus

pytestmark = pytest.mark.integration

SAMPLE = Path(__file__).resolve().parents[2] / "seed" / "samples" / "demo_brief.txt"


async def _seed_corpus(session):
    for abbr, name, minv, maxv, sy, ey, courts in corpus.REPORTERS:
        session.add(
            Reporter(
                abbreviation=abbr, name=name, min_volume=minv, max_volume=maxv,
                start_year=sy, end_year=ey, courts=courts,
            )
        )
    for row in corpus.all_sources():
        session.add(ReferenceSource(embedding=embed(row["searchable_text"]), **row))
    await session.flush()


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_creates_document_and_job(client):
    files = {"file": ("note.txt", b"See Roe v. Wade, 410 U.S. 113 (1973).", "text/plain")}
    resp = await client.post("/api/v1/documents", files=files)
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "note.txt"
    assert body["status"] == "queued"

    listing = await client.get("/api/v1/documents")
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1


@pytest.mark.asyncio
async def test_unsupported_file_rejected(client):
    files = {"file": ("evil.exe", b"MZ", "application/octet-stream")}
    resp = await client.post("/api/v1/documents", files=files)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_full_pipeline_classifies_demo_brief(client, session):
    await _seed_corpus(session)
    await session.commit()

    files = {"file": (SAMPLE.name, SAMPLE.read_bytes(), "text/plain")}
    upload = await client.post("/api/v1/documents", files=files)
    document_id = upload.json()["id"]

    # Simulate the worker running the queued job.
    processing = ProcessingService(session)
    count = await processing.process_document(uuid.UUID(document_id))
    await session.commit()
    assert count >= 8

    dash = await client.get(f"/api/v1/documents/{document_id}/dashboard")
    assert dash.status_code == 200
    stats = dash.json()
    assert stats["total_citations"] == count
    assert stats["verified"] >= 1       # Brown, 42 U.S.C. 1983 ...
    assert stats["hallucinated"] >= 1   # 999 Z.3d / future year / 99 U.S.C.
    assert stats["suspicious"] >= 1     # Roe wrong year, Gideon wrong page
    assert 0.0 <= stats["verification_rate"] <= 1.0

    citations = await client.get(f"/api/v1/documents/{document_id}/citations")
    assert citations.status_code == 200
    results = {c["validation"]["result"] for c in citations.json()}
    assert "verified" in results
    assert "hallucinated" in results


@pytest.mark.asyncio
async def test_reports_download_in_all_formats(client, session):
    await _seed_corpus(session)
    await session.commit()

    files = {"file": ("brief.txt", SAMPLE.read_bytes(), "text/plain")}
    upload = await client.post("/api/v1/documents", files=files)
    document_id = upload.json()["id"]
    await ProcessingService(session).process_document(uuid.UUID(document_id))
    await session.commit()

    rjson = await client.get(f"/api/v1/documents/{document_id}/report.json")
    assert rjson.status_code == 200
    assert rjson.json()["summary"]["total_citations"] >= 8

    rcsv = await client.get(f"/api/v1/documents/{document_id}/report.csv")
    assert rcsv.status_code == 200
    assert rcsv.headers["content-type"].startswith("text/csv")

    rpdf = await client.get(f"/api/v1/documents/{document_id}/report.pdf")
    assert rpdf.status_code == 200
    assert rpdf.content[:5] == b"%PDF-"
