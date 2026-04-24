# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read First

Before writing any code, read these documents in order:

1. `CLAUDE_CODE_HANDOFF.md` -- Complete build guide with architecture, schema, API routes, security, directory structure, and phased build instructions.
2. `docs/SYSTEM_PLAN.md` -- the practitioner's original spec with all knowledge domains, interaction modes, scoring, report structure, and voice guidelines.
3. `~/.claude/CLAUDE.md` -- Secure Build Standard (33 rules). Enforce on every file.

## Project Identity

RAG-powered wellness audit platform for a wellness practitioner. The system acts as the practitioner's diagnostic brain -- guiding structured client audits, synthesizing observations against a curated knowledge base, and generating scored client reports.

**Owner:** Elliot Conner / The Tech-E LLC
**End User:** A wellness practitioner (mobile-first, used in client homes)

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), React 18, TypeScript strict, Tailwind CSS |
| Backend | FastAPI, Python 3.12, async everywhere, Pydantic v2 |
| Database | PostgreSQL 16 via SQLAlchemy 2.0 + asyncpg, migrations with Alembic |
| Vector Store | ChromaDB + BM25 hybrid retrieval (reciprocal rank fusion) |
| Embeddings | BAAI/bge-large-en-v1.5 via sentence-transformers |
| LLM | Claude API -- Opus for diagnosis/reports, Sonnet for classification |
| Auth | JWT (python-jose) + Argon2id (passlib) |
| PDF Export | WeasyPrint (HTML-to-PDF) |
| Logging | structlog with PII redaction and correlation IDs |

## Commands

```bash
# Development: Start infrastructure only (Postgres + ChromaDB)
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d db chromadb

# Production: Start everything with Nginx reverse proxy
docker compose -f docker/docker-compose.yml up -d

# Backend dev server
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend dev server
cd frontend && npm run dev

# Run all backend tests
cd backend && pytest

# Run a single test file
cd backend && pytest tests/test_health.py

# Run tests with coverage
cd backend && pytest --cov=app --cov-report=term-missing

# Database migrations
cd backend && alembic upgrade head
cd backend && alembic revision --autogenerate -m "description"
```

## Architecture

### Backend (FastAPI)

Entry point: `backend/app/main.py`. All routes are registered under `/api/v1/`.

**Layers follow a strict separation:**
- `api/routes/` -- HTTP handlers only. No business logic. Delegate to services.
- `services/` -- Business logic. Key services: `rag.py` (hybrid retrieval pipeline), `ingestion.py` (document chunking and embedding), `diagnosis.py` (Claude Opus scoring), `report_generator.py` (report assembly + PDF), `categorizer.py` (Claude Sonnet auto-categorization for free-form observations), `file_handler.py` (upload validation + EXIF stripping).
- `db/models/` -- SQLAlchemy 2.0 async models. All tables use UUID PKs, UTC timestamps, soft deletes.
- `schemas/` -- Pydantic v2 request/response models. One schema file per domain entity.
- `core/config.py` -- `pydantic-settings` loading from env vars. Single `settings` instance.
- `core/security.py` -- JWT issuance/validation, Argon2id password hashing.

### Frontend (Next.js App Router)

`frontend/src/app/` uses file-based routing. Key routes:
- `/dashboard` -- Main hub with recent sessions and stats
- `/clients/[id]` -- Client detail with session history
- `/audit/[sessionId]/field` -- Mode 1: Structured room-by-room walkthrough
- `/audit/[sessionId]/freeform` -- Mode 2: Free-form observation capture
- `/audit/[sessionId]/report` -- Report preview, edit, approve, export
- `/knowledge/upload` -- Knowledge base document ingestion

Shared components live in `frontend/src/components/`. API client in `frontend/src/lib/api.ts`.

### RAG Pipeline

Documents from `knowledge-base/` (7 domains) are chunked, embedded, and stored in ChromaDB collections. Retrieval uses hybrid search: ChromaDB semantic similarity + BM25 keyword matching, fused via reciprocal rank fusion. Top-K results feed into Claude Opus for diagnosis and report generation.

### Knowledge Base Domains

Seed documents in `knowledge-base/` organized by domain:
1. Well water/environmental, 2. Research, 3. Products, 4. Patterns, 5. Philosophies, 6. Aesthetics, 7. Partners

### Audit Session Flow

`in_progress` -> `observations_complete` -> `diagnosis_pending` -> `report_draft` -> `report_final` -> `closed`

### Docker Services

`docker/docker-compose.yml` runs: `db` (Postgres on :5432), `chromadb` (on :8100 mapped to internal :8000), `backend` (:8000), `frontend` (:3000). ChromaDB port is 8100 externally to avoid conflict with uvicorn.

## Code Style

- Python: type hints on all signatures, Pydantic models for all schemas, async everywhere, structlog, pytest
- TypeScript: strict mode, no `any`, Server Components by default, Tailwind only (no CSS modules), React Hook Form + Zod for validation
- No em dashes in writing (use --)

## Current Phase

Start with **Phase 1: Foundation and Knowledge Ingestion**. Full task list and completion criteria in `CLAUDE_CODE_HANDOFF.md`.
