# CiteCheck

[![CI](https://github.com/marcus-castillo/argus/actions/workflows/ci.yml/badge.svg)](https://github.com/marcus-castillo/argus/actions/workflows/ci.yml)

**Production-quality legal citation validator SaaS.**

Lawyers upload briefs, motions, and memoranda. CiteCheck extracts legal
citations, verifies that cited cases/statutes/regulations actually exist,
checks metadata consistency (volume, reporter, page, year, court), and flags
suspicious or **hallucinated** citations — the kind increasingly produced by
generative-AI legal drafting.

---

## Table of contents

- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [How verification works](#how-verification-works)
- [Quick start (Docker)](#quick-start-docker)
- [Local development](#local-development)
- [Database](#database)
- [API](#api)
- [Testing](#testing)
- [CI](#ci)
- [Seed data](#seed-data)
- [Production notes](#production-notes)

---

## Architecture

CiteCheck follows **clean architecture** with strict layering. Dependencies
point inward; the domain (`app/citation`) knows nothing about the database,
HTTP, or the framework.

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 15 / TS / Tailwind / shadcn-ui)           │
│  typed API client ── lib/api/*                                │
└───────────────┬──────────────────────────────────────────────┘
                │  HTTP (OpenAPI)
┌───────────────▼──────────────────────────────────────────────┐
│  API layer        app/api/v1/*        (FastAPI routers)       │
│  ───────────────────────────────────────────────────────     │
│  Service layer    app/services/*      (use-cases, orchestration)│
│  ───────────────────────────────────────────────────────     │
│  Repository layer app/repositories/*  (data access, SQLAlchemy)│
│  ───────────────────────────────────────────────────────     │
│  Domain           app/citation/*      (pure extraction +      │
│                                        verification engine)   │
│  ───────────────────────────────────────────────────────     │
│  Models           app/models/*        (SQLAlchemy ORM)        │
└───────────────┬──────────────────────────────────────────────┘
                │
        ┌───────▼────────┐        ┌──────────────────────────┐
        │  PostgreSQL +  │        │  Worker (background jobs) │
        │  pgvector      │◄───────┤  polls processing_jobs    │
        └────────────────┘        └──────────────────────────┘
```

### Why a worker container?

Citation verification is I/O- and CPU-bound (PDF parsing, regex extraction,
vector search per citation). Doing it inside the request would block. Instead
the upload endpoint enqueues a `processing_job`; a dedicated worker process
picks it up, runs extraction + verification, and writes results back. The
frontend polls document status.

---

## Tech stack

| Layer        | Choice                                              |
|--------------|-----------------------------------------------------|
| Frontend     | Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui |
| Backend      | FastAPI, Pydantic v2, SQLAlchemy 2.0 (async)        |
| Database     | PostgreSQL 16 + `pgvector`                          |
| Migrations   | Alembic                                             |
| Jobs         | DB-backed queue + asyncio worker                    |
| Parsing      | `pypdf` (PDF), `python-docx` (DOCX)                 |
| Reports      | `reportlab` (PDF), stdlib `csv`/`json`              |
| Container    | Docker Compose                                      |
| CI           | GitHub Actions                                      |

---

## Repository layout

```
citecheck/
├── docker-compose.yml
├── README.md
├── .github/workflows/ci.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/0001_initial.py
│   ├── app/
│   │   ├── main.py
│   │   ├── core/            # config, db, logging
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic DTOs
│   │   ├── repositories/    # repository pattern
│   │   ├── services/        # service layer / use cases
│   │   ├── citation/        # domain: extraction + verification engine
│   │   ├── reports/         # PDF/CSV/JSON report generators
│   │   ├── workers/         # background job worker
│   │   └── api/             # FastAPI routers + deps
│   ├── seed/seed.py         # reference corpus + demo data
│   └── tests/               # unit + integration
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── app/                 # App Router pages
    ├── components/          # UI + shadcn primitives
    ├── lib/                 # typed API client
    └── e2e/                 # Playwright E2E
```

---

## How verification works

For every extracted citation the engine runs a pipeline of independent
**checks**, each returning a finding with a severity. The overall result and a
0–1 confidence score are aggregated from the findings.

1. **Existence** — does a matching case/statute/regulation exist in the source
   corpus? Exact reporter+volume+page lookup, falling back to fuzzy
   case-name + pgvector semantic match.
2. **Reporter validity** — is the reporter abbreviation real (`U.S.`, `F.3d`,
   `S. Ct.`, …)? Unknown reporters are a strong hallucination signal.
3. **Volume plausibility** — is the volume within the published range for that
   reporter?
4. **Page plausibility** — positive, within the volume.
5. **Year consistency** — does the cited year match the source's decision year,
   and is it temporally possible (e.g. a reporter that didn't exist yet)?
6. **Court consistency** — does the cited/inferred court match the reporter and
   the source record?
7. **Format anomalies** — Bluebook-shaped structural checks (missing reporter,
   `v.` spacing, signal noise) that catch fabricated-looking strings.

Confidence aggregation and severity weighting live in
`app/citation/verification/engine.py`.

---

## Quick start (Docker)

```bash
git clone <repo> citecheck && cd citecheck
cp backend/.env.example backend/.env        # optional: tweak settings
docker compose up --build
```

Then:

- Frontend → http://localhost:3000
- API + Swagger → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc

On first boot the `migrate` + `seed` services run automatically (run once,
populate the reference corpus and a demo document).

Upload `backend/seed/samples/demo_brief.txt` from the UI to see verified,
suspicious, and hallucinated citations side by side.

---

## Local development

### Backend

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate    # Windows
pip install -e ".[dev]"
export DATABASE_URL=postgresql+asyncpg://citecheck:citecheck@localhost:5432/citecheck
alembic upgrade head
python -m seed.seed
uvicorn app.main:app --reload
# in another shell, run the worker:
python -m app.workers.worker
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## Database

See [`backend/alembic/versions/0001_initial.py`](backend/alembic/versions/0001_initial.py)
for the authoritative schema. Core tables:

| Table              | Purpose                                              |
|--------------------|------------------------------------------------------|
| `documents`        | Uploaded files + processing status                   |
| `citations`        | Extracted citations + parsed metadata                |
| `validations`      | One verification result per citation (result, score) |
| `validation_findings` | Per-check findings backing a validation           |
| `reference_sources`| Seeded corpus of real cases/statutes/regs (+ embedding) |
| `reporters`        | Reporter registry (abbrev, name, volume range, years)|
| `processing_jobs`  | Background job queue                                  |

`reference_sources.embedding` is a `vector(384)` column (pgvector) for semantic
fallback matching.

---

## API

Full interactive docs at `/docs`. Highlights:

| Method | Path                                  | Description                       |
|--------|---------------------------------------|-----------------------------------|
| POST   | `/api/v1/documents`                   | Upload (pdf/docx/txt), enqueue job|
| GET    | `/api/v1/documents`                   | List documents                    |
| GET    | `/api/v1/documents/{id}`              | Document + status                 |
| GET    | `/api/v1/documents/{id}/citations`    | Citations + validations           |
| GET    | `/api/v1/documents/{id}/dashboard`    | Aggregated stats                  |
| GET    | `/api/v1/documents/{id}/report.pdf`   | PDF report                        |
| GET    | `/api/v1/documents/{id}/report.csv`   | CSV report                        |
| GET    | `/api/v1/documents/{id}/report.json`  | JSON report                       |
| GET    | `/api/v1/health`                      | Liveness/readiness                |

---

## Testing

```bash
cd backend
pytest                       # unit + integration
pytest -m unit               # extraction/verification units only
pytest -m integration        # API + repository (needs Postgres)

cd ../frontend
npm run test                 # vitest unit
npm run test:e2e             # Playwright E2E (needs stack up)
```

- **Unit**: extraction regexes, each verification check, confidence aggregation,
  report serializers.
- **Integration**: upload→job→verify→dashboard flow against a real Postgres.
- **E2E**: Playwright drives upload → dashboard → report download.

---

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push/PR:

- Backend: ruff lint, mypy, pytest (with a Postgres+pgvector service container).
- Frontend: eslint, tsc, vitest, `next build`.
- Playwright E2E against a Compose-booted stack.

---

## Seed data

`python -m seed.seed` loads:

- The **reporter registry** (`U.S.`, `S. Ct.`, `L. Ed.`, `F.`, `F.2d`, `F.3d`,
  `F. Supp.`, …) with volume ranges and active years.
- A **reference corpus** of landmark cases (Brown, Roe, Miranda, Gideon,
  Marbury, Obergefell, …), key statutes (`42 U.S.C. § 1983`, …) and regs.
- A **demo document** containing a mix of valid, metadata-inconsistent, and
  fully hallucinated citations so the dashboard is populated on first run.

---

## Production notes

- Swap the local `ReferenceCorpusProvider` for a `WestlawProvider` /
  `CourtListenerProvider` by implementing `app/citation/sources/base.py`.
- The embedding function in `app/citation/embeddings.py` is a deterministic
  hashing embedder so the stack runs with zero external model downloads; swap
  in `sentence-transformers` for production-grade semantic matching.
- Add auth (the schema is multi-tenant-ready via `documents.owner_id`).
