# WellnessOps

> A multi-modal RAG platform for in-home wellness audits — hybrid retrieval, two capture modes, AI-scored reports, and PDF deliverables.

**The pitch in one paragraph.** WellnessOps is a mobile-first audit platform for wellness practitioners conducting in-home assessments. It supports two capture modes (structured room-by-room walkthrough and free-form observation), retrieves expert knowledge from a hybrid vector + BM25 pipeline across seven domains (environment, research, products, patterns, philosophies, aesthetics, partners), and uses Claude Opus to generate scored reports with prioritized recommendations, product suggestions, and partner referrals. Reports are editable, practitioner-overridable, and exported as branded PDFs.

This is a domain-agnostic RAG/agent system — the same retrieval, scoring, and report-generation patterns apply to any field with structured expert knowledge and client-facing deliverables.

---

## Why this exists

Most "AI wellness apps" are either generic chatbots or one-size-fits-all assessments. Practitioners who do real in-home audits need something different:

1. A **mobile-first capture surface** they can use one-handed in a client's living room
2. **Two capture modes** — guided when they want structure, free-form when they want to dictate observations
3. **Knowledge-grounded reasoning** that draws from *their* curated body of expertise, not Wikipedia
4. **Scored, branded reports** that look like the practitioner wrote them
5. **Final-say authority** on every score the AI generates

WellnessOps is the system version of that workflow.

---

## What's interesting about it (engineering)

| Component | Implementation | Why it matters |
|---|---|---|
| **Retrieval** | ChromaDB (vector, bge-large-en-v1.5) + BM25 + Reciprocal Rank Fusion | Vector-only retrieval misses exact-name queries (product names, partner specialties). Hybrid lifts precision. |
| **Two capture modes** | Structured "Field Companion" prompts (room-by-room) + free-form text/voice with Claude Sonnet auto-categorization | Practitioners use both — structured for thoroughness, free-form for flow. Same backend. |
| **Diagnosis engine** | Claude Opus over retrieved context, scores 10 categories on a 100-point scale, generates per-category recommendations | Scoring is grounded in the practitioner's knowledge base, not the model's general training. |
| **Practitioner override** | Every AI-generated score is editable. Original `ai_generated_score` is preserved alongside the override for calibration tracking. | Builds a labeled dataset of practitioner expertise over time — usable for future fine-tuning or prompt improvement. |
| **Report generation** | Templated HTML rendered through WeasyPrint to branded PDF | Practitioner can edit any section before export. |
| **Security** | JWT + Argon2id, EXIF stripping on photo uploads, file-type validation by magic bytes, structlog with PII redaction, 33-rule Secure Build Standard enforced | Audit data is sensitive (home photos, health observations). Treated accordingly. |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          WELLNESSOPS                                 │
│                                                                      │
│  ┌──────────────────────┐     ┌──────────────────────────────┐      │
│  │  Knowledge Base      │     │   Capture Modes              │      │
│  │  (7 domains)         │     │                              │      │
│  │                      │     │  • Field Companion           │      │
│  │  • Environment       │     │    (room-by-room prompts)    │      │
│  │  • Research          │     │                              │      │
│  │  • Products          │     │  • Free-form Observation     │      │
│  │  • Patterns          │     │    (text + photo + voice)    │      │
│  │  • Philosophies      │     │                              │      │
│  │  • Aesthetics        │     │  Both feed the same          │      │
│  │  • Partners          │     │  observation table.          │      │
│  └──────────┬───────────┘     └──────────────┬───────────────┘      │
│             │                                 │                      │
│  ┌──────────▼─────────────────────────────────▼───────────────────┐ │
│  │  Hybrid Retrieval (ChromaDB + BM25 + RRF fusion)               │ │
│  └──────────────────────────────────┬─────────────────────────────┘ │
│                                     │                                │
│  ┌──────────────────────────────────▼─────────────────────────────┐ │
│  │  Diagnosis Engine (Claude Opus)                                │ │
│  │  • Per-category scoring (10 categories, 100-point scale)       │ │
│  │  • Why-this-matters justification (knowledge-grounded)         │ │
│  │  • How-to-close-gap recommendations                            │ │
│  └──────────────────────────────────┬─────────────────────────────┘ │
│                                     │                                │
│  ┌──────────────────────────────────▼─────────────────────────────┐ │
│  │  Practitioner Review                                           │ │
│  │  • Override any score with notes (delta tracked for calibration)│ │
│  │  • Edit any report section                                     │ │
│  │  • Approve and export                                          │ │
│  └──────────────────────────────────┬─────────────────────────────┘ │
│                                     │                                │
│  ┌──────────────────────────────────▼─────────────────────────────┐ │
│  │  Report Generation (WeasyPrint → branded PDF)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 14 App Router, React 18, TypeScript strict, Tailwind CSS | Mobile-first SSR, file-based routing |
| Backend | FastAPI, Python 3.12, async everywhere | Async I/O for retrieval + LLM calls |
| Database | PostgreSQL 16, SQLAlchemy 2.0 async, Alembic | UUID PKs, UTC timestamps, soft deletes |
| Vector store | ChromaDB | Embedded, low ops |
| Keyword search | rank-bm25 | Hybrid retrieval alongside vectors |
| Embeddings | BAAI/bge-large-en-v1.5 (1024-dim) | Strong open-source model |
| Reasoning LLM | Claude Opus (Anthropic API) | Scoring, report generation |
| Classification LLM | Claude Sonnet | Free-form observation auto-categorization |
| Auth | JWT (python-jose) + Argon2id (passlib) | Compliance with secure auth standards |
| Validation | Pydantic v2 | Type-safe schemas |
| Logging | structlog with PII redaction | Structured JSON, redacts sensitive fields |
| PDF export | WeasyPrint | HTML → branded PDF |
| Testing | pytest + pytest-asyncio | Async-first test support |
| Container | Docker Compose (Postgres + ChromaDB + backend + frontend + Nginx) | Single-command local stack |

---

## Repository layout

```
wellness-ops/
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── api/routes/      # HTTP handlers (no business logic)
│   │   ├── services/        # Business logic: rag, diagnosis, report_generator, ingestion
│   │   ├── db/models/       # SQLAlchemy 2.0 async models
│   │   ├── schemas/         # Pydantic v2 request/response models
│   │   ├── core/            # config, security (JWT, Argon2id)
│   │   └── templates/       # Report HTML templates
│   ├── alembic/             # DB migrations
│   └── tests/               # pytest async tests
├── frontend/                 # Next.js 14 App Router
│   ├── src/app/             # File-based routes
│   ├── src/components/      # Shared React components
│   └── src/lib/             # API client
├── docker/                   # docker-compose for prod and dev
├── knowledge-base/           # 7 domain folders for RAG corpus
├── scripts/                  # Seed scripts, SSL setup
├── e2e/                      # Playwright E2E tests
└── docs/                     # API, schema, methodology, prompts, report structure
```

---

## Quick start

```bash
# Start the full stack (Postgres + ChromaDB + backend + frontend)
docker compose -f docker/docker-compose.yml up -d

# Or run services individually
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev

# Apply migrations
cd backend && alembic upgrade head

# Seed an admin user, then load demo data
PYTHONPATH=backend python scripts/seed_db.py
PYTHONPATH=backend python scripts/seed_demo.py
```

App at `http://localhost:3000`. API at `http://localhost:8000`. ChromaDB at `http://localhost:8100`.

---

## RAG pipeline

Documents in `knowledge-base/` are organized into 7 domain folders. Each document is:

1. **Parsed** by file type (Markdown, PDF, plain text)
2. **Chunked** at 1500 chars with 200-char overlap (1500/200 outperformed 500/50 on long-form wellness documents — smaller chunks fragmented context and inflated index size)
3. **Embedded** with bge-large-en-v1.5 (1024-dim)
4. **Indexed** to a ChromaDB collection (per domain) and a parallel BM25 index

At query time:
1. Hybrid search runs vector + BM25 in parallel
2. Reciprocal Rank Fusion merges results
3. Top-K chunks (default 8) feed Claude Opus alongside the audit observation set
4. Opus generates per-category scores, justifications, and recommendations

---

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/SYSTEM_PLAN.md`](docs/SYSTEM_PLAN.md) | High-level system overview |
| [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) | Full database schema |
| [`docs/API_ROUTES.md`](docs/API_ROUTES.md) | REST endpoint reference |
| [`docs/REPORT_STRUCTURE.md`](docs/REPORT_STRUCTURE.md) | Client report format |
| [`docs/FIELD_COMPANION_PROMPTS.md`](docs/FIELD_COMPANION_PROMPTS.md) | Structured intake prompts |
| [`docs/SCORING_METHODOLOGY.md`](docs/SCORING_METHODOLOGY.md) | Scoring criteria |
| [`CLAUDE_CODE_HANDOFF.md`](CLAUDE_CODE_HANDOFF.md) | Build guide for Claude Code |

---

## Status

| Phase | Status | Notes |
|---|---|---|
| Foundation + Knowledge Ingestion | ✅ | Auth, multi-domain ingestion, hybrid retrieval |
| Field Companion (Structured Intake) | ✅ | Room-by-room guided walkthrough |
| Free-Form Capture | ✅ | Sonnet-powered auto-categorization |
| Diagnosis Engine + Report Generation | ✅ | Opus scoring, WeasyPrint PDF export |
| Pattern Recognition | 🚧 | Cross-engagement pattern detection |
| Partner Ecosystem + Polish | 🚧 | Partner referral matching |

---

## License

Proprietary — Elliot Conner / The Tech-E LLC
