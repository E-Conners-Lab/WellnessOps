# WellnessOps — Claude Code Build Guide

## What This Document Is

This is the complete build guide for **WellnessOps**, a RAG-powered wellness audit platform. You (Claude Code) are building this from scratch. The end user is a wellness practitioner who conducts in-home audits. This system acts as the practitioner's diagnostic brain — guiding structured client audits, synthesizing observations against a curated knowledge base, generating scored client reports, and surfacing patterns across engagements.

**Read the full spec first:** `docs/SYSTEM_PLAN.md` contains the practitioner's complete system plan with all seven knowledge domains, three interaction modes, scoring methodology, report structure, and voice guidelines. Every architectural decision below derives from that document.

**Read the security standard:** This project enforces the Secure Build Standard at `~/.claude/CLAUDE.md` (33 rules, 7 domains). Reference it before writing any backend code, auth flows, file handling, or deployment configs.

---

## Project Identity

- **Owner:** Elliot Conner / The Tech-E LLC
- **End User:** the wellness practitioner (sole practitioner initially, mobile-first usage in client homes)
- **Client:** WellnessOps (wellnessops.local)
- **Repo name:** `wellness-ops`

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 14+ (App Router), React 18+, TypeScript, Tailwind CSS | Mobile-first, Server Components, proven stack |
| Backend | FastAPI (Python 3.12+), async everywhere | Fast API development, async native, Pydantic validation |
| Database | PostgreSQL 16 via SQLAlchemy 2.0 + asyncpg | Structured data, JSONB support, proven |
| Migrations | Alembic | SQLAlchemy-native migration tool |
| Vector Store | ChromaDB | RAG retrieval, 7 domain collections |
| Retrieval | ChromaDB + BM25 (rank_bm25), reciprocal rank fusion | Hybrid semantic + keyword search |
| Embeddings | BAAI/bge-large-en-v1.5 via sentence-transformers | High quality, already proven in Engineer Brain project |
| LLM | Claude API — Opus for diagnosis/reports, Sonnet for classification | Reasoning quality for reports, speed for tagging |
| File Storage | Local filesystem (dev), S3-compatible (prod) | Photos, documents, generated PDFs |
| PDF Export | WeasyPrint | HTML-to-PDF with CSS styling support |
| Auth | JWT (python-jose) + Argon2id (passlib) | Stateless auth, strong hashing |
| Logging | structlog | Structured JSON logs with correlation IDs |
| Containerization | Docker Compose (dev), Kubernetes (prod) | Local dev parity, production on Proxmox cluster |

---

## Code Style Rules

- Readability first. Meaningful names. Test-driven. DRY but not at the cost of clarity.
- Fail loud. No silent exception swallowing.
- Simplicity over cleverness. Descriptive commits. Clean architecture. Docs current.
- **Python:** Type hints on all function signatures. Pydantic models for all request/response schemas. Async everywhere. Structured logging with correlation IDs. Tests with pytest + pytest-asyncio.
- **TypeScript:** Strict mode. No `any` types without documented justification. Server Components by default. Tailwind CSS only (no CSS modules). React Hook Form + Zod for validation.
- **Writing style (for all docs, comments, README):** No em dashes. Paragraph form over bullet points where possible. Peer-to-peer conversational tone.

---

## Security Requirements (Non-Negotiable)

These come from the Secure Build Standard. Enforce on every file you write:

- **SEC-01:** No sensitive data in localStorage. Sessions use secure httpOnly cookies.
- **SEC-02/03:** Auth on every non-public endpoint. Authz (ownership) checked on every data operation.
- **SEC-05:** Server-side validation on all inputs. Client-side is UX only.
- **SEC-06:** Rate limit login, signup, password reset, and sensitive APIs.
- **SEC-07:** CSRF protection on all state-changing requests.
- **SEC-08:** HTTPS enforced. HTTP redirected.
- **SEC-09/10/25:** CSP, X-Frame-Options, and strict Referrer-Policy headers.
- **SEC-11:** No stack traces or debug info in production responses. Return correlation IDs.
- **SEC-12/18:** No secrets in code, logs, bundles, or prompts. No logging of tokens or PII.
- **SEC-13:** Separate credentials per environment.
- **SEC-15/16:** Tokens scoped to minimum permissions. Short-lived access tokens (15 min). Refresh token rotation.
- **SEC-17:** Passwords hashed with Argon2id.
- **SEC-20:** Signed URLs for private file access (client photos, financial docs). Short expiry.
- **SEC-21/22:** Strip EXIF metadata from uploaded photos. Validate file type (magic bytes), size, and content.
- **SEC-27:** Never trust client-supplied IDs without verifying ownership server-side.
- **SEC-28:** Audit log for login, client data access, report generation, admin actions, deletes, permission changes.
- **SEC-29/30:** Pin dependency versions. Scan before deploy.

---

## Directory Structure

Build this structure. Every file gets created as you work through each phase.

```
wellness-ops/
├── CLAUDE.md                          # Project-level instructions (you maintain this)
├── README.md
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt               # Pinned versions (SEC-30)
│   ├── alembic.ini
│   ├── alembic/                        # Migration scripts
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py         # Auth deps, DB session deps
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       ├── auth.py
│   │   │       ├── clients.py
│   │   │       ├── audits.py
│   │   │       ├── observations.py
│   │   │       ├── knowledge.py
│   │   │       ├── reports.py
│   │   │       ├── products.py
│   │   │       └── partners.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Pydantic Settings from env
│   │   │   ├── security.py            # JWT, password hashing, auth utils
│   │   │   └── logging.py             # structlog setup with PII redaction
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # Async engine, session factory
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       ├── base.py            # Declarative base, common mixins
│   │   │       ├── user.py
│   │   │       ├── client.py
│   │   │       ├── audit.py
│   │   │       ├── observation.py
│   │   │       ├── score.py
│   │   │       ├── report.py
│   │   │       ├── product.py
│   │   │       ├── partner.py
│   │   │       ├── knowledge.py
│   │   │       └── audit_log.py
│   │   ├── schemas/                    # Pydantic request/response models
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── client.py
│   │   │   ├── audit.py
│   │   │   ├── observation.py
│   │   │   ├── score.py
│   │   │   ├── report.py
│   │   │   ├── product.py
│   │   │   ├── partner.py
│   │   │   └── knowledge.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── rag.py                 # RAG pipeline: ChromaDB + BM25 hybrid retrieval
│   │   │   ├── ingestion.py           # Document chunking, embedding, ChromaDB storage
│   │   │   ├── diagnosis.py           # Claude Opus scoring and diagnosis logic
│   │   │   ├── report_generator.py    # Report assembly and PDF export
│   │   │   ├── categorizer.py         # Claude Sonnet auto-categorization (Mode 2)
│   │   │   ├── file_handler.py        # Upload processing, EXIF strip, validation
│   │   │   ├── pattern_matcher.py     # Phase 5: cross-client pattern recognition
│   │   │   └── audit_logger.py        # Immutable audit log writer (SEC-28)
│   │   ├── templates/
│   │   │   └── reports/               # HTML templates for PDF generation
│   │   │       ├── base.html
│   │   │       └── client_report.html
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── text_processing.py     # Chunking, text extraction helpers
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Fixtures: test DB, test client, auth helpers
│       ├── test_health.py
│       ├── test_auth.py
│       ├── test_clients.py
│       ├── test_audits.py
│       ├── test_observations.py
│       ├── test_knowledge.py
│       ├── test_rag.py
│       ├── test_reports.py
│       └── test_file_handler.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout with mobile shell
│   │   │   ├── page.tsx               # Landing/login redirect
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx           # Main dashboard: recent sessions, stats
│   │   │   ├── clients/
│   │   │   │   ├── page.tsx           # Client list
│   │   │   │   ├── new/page.tsx       # New client form
│   │   │   │   └── [id]/page.tsx      # Client detail with session history
│   │   │   ├── audit/
│   │   │   │   ├── [sessionId]/
│   │   │   │   │   ├── page.tsx       # Audit session hub (choose mode, see progress)
│   │   │   │   │   ├── field/page.tsx # Mode 1: Field Companion structured flow
│   │   │   │   │   ├── freeform/page.tsx # Mode 2: Free-form capture
│   │   │   │   │   ├── scores/page.tsx   # Score review and override
│   │   │   │   │   └── report/page.tsx   # Report preview, edit, approve, export
│   │   │   ├── knowledge/
│   │   │   │   ├── page.tsx           # Knowledge base dashboard (domain stats)
│   │   │   │   └── upload/page.tsx    # Document upload and ingestion
│   │   │   ├── products/
│   │   │   │   └── page.tsx           # Product catalog management
│   │   │   └── partners/
│   │   │       └── page.tsx           # Partner directory management
│   │   ├── components/
│   │   │   ├── ui/                    # Shared primitives (Button, Input, Card, Modal, etc.)
│   │   │   ├── layout/
│   │   │   │   ├── MobileNav.tsx      # Bottom nav for mobile
│   │   │   │   ├── Sidebar.tsx        # Desktop sidebar
│   │   │   │   └── AppShell.tsx       # Responsive shell (sidebar on desktop, bottom nav on mobile)
│   │   │   ├── audit/
│   │   │   │   ├── RoomSection.tsx    # Collapsible room section with prompts
│   │   │   │   ├── ObservationInput.tsx # Text + photo input for single prompt
│   │   │   │   ├── ProgressBar.tsx    # Session completion indicator
│   │   │   │   ├── PhotoUpload.tsx    # Camera/gallery photo upload
│   │   │   │   └── FreeFormInput.tsx  # Mode 2 free-form text/photo input
│   │   │   ├── scores/
│   │   │   │   ├── ScoreCard.tsx      # Individual category score display
│   │   │   │   ├── ScoreOverride.tsx  #the practitioner override input
│   │   │   │   └── OverallScore.tsx   # Big score display with label
│   │   │   ├── reports/
│   │   │   │   ├── ReportPreview.tsx  # Full report rendered in browser
│   │   │   │   └── ReportSection.tsx  # Editable report section
│   │   │   └── knowledge/
│   │   │       ├── DomainCard.tsx     # Domain stats display
│   │   │       └── UploadForm.tsx     # Document upload with domain/tag selection
│   │   ├── lib/
│   │   │   ├── api.ts                 # API client (fetch wrapper with auth)
│   │   │   └── utils.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useAuditSession.ts
│   │   │   └── useDebounce.ts
│   │   ├── types/
│   │   │   └── index.ts              # All TypeScript interfaces
│   │   └── styles/
│   │       └── globals.css
│   └── public/
│       └── assets/                    # WellnessOps branding assets
├── knowledge-base/                    # Seed documents organized by domain
│   ├── domain-1-well/
│   ├── domain-2-research/
│   ├── domain-3-products/
│   ├── domain-4-patterns/
│   ├── domain-5-philosophies/
│   ├── domain-6-aesthetics/
│   └── domain-7-partners/
├── docs/
│   ├── SYSTEM_PLAN.md       # the practitioner's original spec (source of truth)
│   ├── DATABASE_SCHEMA.md
│   ├── REPORT_STRUCTURE.md
│   ├── API_ROUTES.md
│   ├── FIELD_COMPANION_PROMPTS.md
│   └── SCORING_METHODOLOGY.md
└── scripts/
    ├── seed_db.py                     # Create initial user, sample data
    ├── seed_knowledge.py              # Ingest seed documents from knowledge-base/
    └── generate_test_data.py          # Generate fake client/session data for testing
```

---

## Database Schema

All tables use UUID primary keys. Timestamps are UTC. Soft deletes where appropriate.

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'practitioner',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### clients
```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    display_name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    pii_consent BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    budget_tier VARCHAR(50),
    has_wearable BOOLEAN DEFAULT false,
    wearable_type VARCHAR(100),
    financial_audit_consent BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_clients_user_id ON clients(user_id);
```

### audit_sessions
```sql
CREATE TABLE audit_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    user_id UUID NOT NULL REFERENCES users(id),
    audit_tier VARCHAR(20) NOT NULL DEFAULT 'core',
    status VARCHAR(30) NOT NULL DEFAULT 'in_progress',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_sessions_client_id ON audit_sessions(client_id);
CREATE INDEX idx_audit_sessions_status ON audit_sessions(status);
```

Session status flow: `in_progress → observations_complete → diagnosis_pending → report_draft → report_final → closed`

### observations
```sql
CREATE TABLE observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES audit_sessions(id),
    room_area VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    observation_type VARCHAR(30) NOT NULL DEFAULT 'text',
    content TEXT,
    photo_path VARCHAR(500),
    photo_thumbnail_path VARCHAR(500),
    is_from_structured_flow BOOLEAN NOT NULL DEFAULT true,
    auto_categorized BOOLEAN NOT NULL DEFAULT false,
    domain_tags VARCHAR(50)[],
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_observations_session_id ON observations(session_id);
```

### category_scores
```sql
CREATE TABLE category_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES audit_sessions(id),
    category_key VARCHAR(100) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 10),
    ai_generated_score INTEGER,
    status_label VARCHAR(50) NOT NULL,
    what_observed TEXT,
    why_it_matters TEXT,
    how_to_close_gap TEXT,
    is_extended_category BOOLEAN NOT NULL DEFAULT false,
    practitioner_override BOOLEAN NOT NULL DEFAULT false,
    override_notes TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, category_key)
);
```

### reports
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES audit_sessions(id),
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    overall_score INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    overall_label VARCHAR(50) NOT NULL,
    priority_action_plan JSONB,
    vision_section TEXT,
    next_steps TEXT,
    pdf_path VARCHAR(500),
    generated_by VARCHAR(50) NOT NULL DEFAULT 'system',
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, version)
);
```

### products
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    price_range VARCHAR(50),
    purchase_link TEXT,
    why_recommended TEXT NOT NULL,
    best_for TEXT,
    contraindications TEXT,
    practitioner_note TEXT,
    is_recommended BOOLEAN NOT NULL DEFAULT true,
    not_recommended_reason TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### partners
```sql
CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    website VARCHAR(500),
    why_recommended TEXT NOT NULL,
    best_for_client_type TEXT,
    pricing_tier VARCHAR(50),
    is_ambassador BOOLEAN NOT NULL DEFAULT false,
    practitioner_note TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### knowledge_documents
```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    source VARCHAR(500),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    tags VARCHAR(100)[],
    chunk_count INTEGER NOT NULL DEFAULT 0,
    chromadb_collection VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ,
    ingestion_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_knowledge_documents_domain ON knowledge_documents(domain);
CREATE INDEX idx_knowledge_documents_tags ON knowledge_documents USING GIN(tags);
```

### report_product_refs / report_partner_refs
Junction tables linking reports to recommended products and partners. Include `category_key` and `sort_order`.

### audit_log
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
```

---

## ChromaDB Collections (7 Knowledge Domains)

| Collection Name | Domain | Metadata Fields |
|---|---|---|
| `domain_well` | WELL Building Standard | concept (air/water/nourishment/light/movement/thermal/sound/materials/mind/community), section, threshold_type |
| `domain_research` | Articles & Research | topic_tags[], source, publish_date, study_type |
| `domain_products` | Product Recommendations | category, price_range, is_recommended |
| `domain_patterns` | Client Patterns | pattern_type, symptom_tags[], cause_tags[], frequency |
| `domain_philosophies` | Lifestyle Philosophies | philosophy (blue_zones/wabi_sabi/hygge/ikigai/lagom/slow_living/biophilic), principle |
| `domain_aesthetics` | Art & Aesthetics | topic (color_psychology/spatial_composition/texture/materiality), medium |
| `domain_partners` | Partners & Vendors | category, location, pricing_tier |

**Embedding model:** BAAI/bge-large-en-v1.5
**Chunk size:** 512 tokens, 50-token overlap
**Retrieval:** Hybrid search — ChromaDB cosine similarity + BM25 keyword ranking. Merge results with reciprocal rank fusion. Return top 10.

---

## API Routes

Base: `/api/v1`. All routes require JWT auth unless marked PUBLIC.

**Auth (PUBLIC):** POST /auth/login, POST /auth/logout, POST /auth/refresh
**Health (PUBLIC):** GET /health, GET /health/db, GET /health/chroma
**Clients:** GET/POST /clients, GET/PUT/DELETE /clients/{id}, GET /clients/{id}/sessions, POST /clients/{id}/export
**Audits:** POST /audits, GET/PUT /audits/{id}, PUT /audits/{id}/status, GET /audits/{id}/progress, GET /audits/{id}/scores, POST /audits/{id}/scores/generate, POST /audits/{id}/reports/generate
**Observations:** POST /audits/{id}/observations, PUT/DELETE /observations/{id}, POST /audits/{id}/observations/bulk, POST /observations/categorize
**Reports:** GET /reports/{id}, PUT /reports/{id}, PUT /reports/{id}/approve, GET /reports/{id}/pdf, GET /reports/{id}/preview
**Knowledge:** GET/POST /knowledge/documents, GET/DELETE /knowledge/documents/{id}, GET /knowledge/domains, POST /knowledge/search
**Products:** GET/POST /products, PUT/DELETE /products/{id}
**Partners:** GET/POST /partners, PUT/DELETE /partners/{id}

**Standard response:** `{ "status": "success", "data": {...}, "meta": { "page": 1, "per_page": 20, "total": 45 } }`
**Error response (SEC-11):** `{ "status": "error", "message": "Human-readable message", "correlation_id": "uuid" }` — never expose stack traces.

---

## Field Companion Prompt Sequences

These drive Mode 1. Each prompt has a `key`, `room_area`, and `prompt_text`. The UI presents them one at a time on mobile. Each accepts text input, photo upload, or skip.

**Entry and Curb Appeal:** entry_first_impression, entry_communication, entry_threshold
**Living Spaces:** living_dominant_feeling, living_natural_light, living_art_objects, living_biophilic, living_sensory, living_ergonomics, living_seating
**Kitchen:** kitchen_fridge, kitchen_food_system, kitchen_setup, kitchen_eating_location, kitchen_meal_planning, kitchen_pantry
**Hidden Spaces:** hidden_closet, hidden_junk_drawer, hidden_under_sink, hidden_unseen
**Bedroom:** bedroom_visible_from_bed, bedroom_nightstand, bedroom_light, bedroom_temp_humidity, bedroom_work_visible, bedroom_last_sight
**Workspace:** workspace_dedicated, workspace_lighting, workspace_chair, workspace_sightline, workspace_separation
**Extended (Tier 2/3):** extended_books, extended_art, extended_vehicle, extended_office
**Wearable Data:** wearable_device, wearable_sleep, wearable_hrv, wearable_stress, wearable_patterns
**Financial (advanced):** financial_statements, financial_top_categories, financial_alignment, financial_contradictions
**Client Questions:** client_primary_concern, client_already_tried, client_ideal_life, client_answer_patterns, client_between_lines

Store each prompt's full text in a config file or constants module. The complete prompt text for each key is in `docs/SYSTEM_PLAN.md` under "Structured prompt sequence."

---

## Scoring Methodology

**Core Audit:** 10 categories x 10 points = 100 total. Categories marked N/A excluded, denominator adjusts.
**Extended Audit:** 15 categories, same formula.

**Overall score formula:** `(sum of applicable scores / (applicable_count * 10)) * 100`, rounded to nearest integer.

**10 Core categories:** setup_vs_goals, intention, hidden_spaces, kitchen_flow, natural_elements, sleep_environment, movement, sensory, financial_alignment, wearable_data

**5 Extended categories:** ergonomics, art_aesthetic, library_learning, vehicle, workspace

**Overall labels:** 90-100 Thriving, 75-89 Intentional, 60-74 Developing, 45-59 Misaligned, Below 45 Survival Mode

**Category labels:** 10 Exceptional, 8-9 Strong, 6-7 Adequate, 4-5 Problematic, 2-3 Significant issue, 1 Critical

**AI generation process:**
1. Collect all observations for session, grouped by category.
2. For each category, retrieve relevant chunks from all 7 ChromaDB domains.
3. Send observations + knowledge context + scoring criteria to Claude Opus.
4. Claude generates: score, status_label, what_observed, why_it_matters, how_to_close_gap.
5. Match relevant products (Domain 3) and partners (Domain 7) to each category.
6. Present all scores tothe practitioner for review/override before report generation.

**The practitioner override:** She can change any score with notes. AI-generated score preserved in `ai_generated_score` for calibration tracking over time.

---

## Report Structure

See `docs/SYSTEM_PLAN.md` for the practitioner's complete report spec. Key sections:

1. **Header:** Client name/code, date, tier, the practitioner's credentials, branding.
2. **Overall Score:** X/100 with qualitative label.
3. **Category Scores:** Each with score/10, status, what_observed, why_it_matters, how_to_close_gap, products, partners.
4. **Priority Action Plan:** Top 5 by impact.
5. **What Changes When You Fix This:** Written in the practitioner's voice. Paints the vision of life after implementation.
6. **Recommended Partners and Products:** Consolidated list from all categories.
7. **Next Steps:** Clear instructions, how to reachthe practitioner for implementation support.

**PDF requirements:** Clean branded layout. Score visualizations (progress bars or radial charts). Photo thumbnails. Table of contents for extended audits. Footer with page numbers. Filename: `{client}_Wellness_Audit_{date}.pdf`.

---

## the practitioner's Voice Guidelines (for all Claude API prompts that generate client-facing text)

**Always:** Direct, warm, specific, occasionally funny, never clinical. Sounds like a trusted expert who genuinely cares. Plain language. Prioritize by impact not comprehensiveness. Distinguish root causes from surface symptoms. Every client is unique. The missing link is almost never the recommendation, it is implementation.

**Never:** Suggest productsthe practitioner has not vetted. Make medical diagnoses. Overwhelm with more than 5 priority recommendations. Shame or judge the client. Treat the client as a collection of problems rather than a whole person.

---

## Build Phases — Execute in Order

### Phase 1: Foundation and Knowledge Ingestion

**Goal:** Backend running with database, ChromaDB, document ingestion pipeline, knowledge admin UI, auth, and Docker Compose.

**Backend tasks:**
1. Initialize FastAPI app with health checks, CORS, structured logging with correlation IDs.
2. Set up SQLAlchemy async engine + session factory for PostgreSQL.
3. Create Alembic config and initial migration with tables: users, knowledge_documents, audit_log.
4. Implement auth system: login (Argon2id), logout, JWT in httpOnly cookies, refresh rotation (SEC-01, SEC-04, SEC-16, SEC-17).
5. Add security headers middleware: CSP, X-Frame-Options, Referrer-Policy, Cache-Control (SEC-09, SEC-10, SEC-24, SEC-25).
6. Add rate limiting on auth endpoints (SEC-06).
7. Add audit log service — write-only, logs all auth events and knowledge operations (SEC-28).
8. Set up ChromaDB client and create all 7 domain collections with metadata schemas.
9. Build document ingestion pipeline: upload file → extract text → chunk (512 tokens, 50 overlap) → embed (bge-large-en-v1.5) → store in ChromaDB → update knowledge_documents in PostgreSQL.
10. Build knowledge management routes: list documents, upload/ingest, get document with chunk preview, delete document.
11. Build hybrid RAG search: ChromaDB semantic + BM25 keyword → reciprocal rank fusion → return top K.
12. File upload handler with validation (SEC-22) and EXIF stripping (SEC-21).
13. Seed script for initial admin user.
14. Docker Compose with PostgreSQL, ChromaDB, and backend services.
15. Tests for auth, knowledge ingestion, RAG retrieval, file handling.

**Frontend tasks:**
1. Initialize Next.js 14 with App Router, TypeScript strict, Tailwind CSS.
2. Build responsive AppShell: sidebar on desktop, bottom nav on mobile.
3. Login page.
4. Knowledge base dashboard: domain cards showing doc count and chunk count per domain.
5. Document upload page: file picker, domain selector, tag input, ingestion status.
6. API client with auth token handling.

**Done when:**the practitioner can log in, upload a document to any of the 7 domains, see it reflected in the domain stats, and the ingestion pipeline processes it into ChromaDB. RAG search returns relevant chunks. All running in Docker Compose.

---

### Phase 2: Field Companion Mode (Structured Intake)

**Goal:**the practitioner can create clients, start audit sessions, and walk through the room-by-room structured prompt flow on her phone.

**Backend tasks:**
1. Alembic migration: add clients, audit_sessions, observations tables.
2. Client CRUD routes with ownership enforcement (SEC-03, SEC-27).
3. Audit session routes: create, update, advance status, get progress.
4. Observation routes: add (text/photo), edit, delete, bulk add.
5. Photo upload route with EXIF stripping, thumbnail generation, and signed URL retrieval (SEC-20, SEC-21).
6. Session progress calculation: completion % per room section.
7. Client data export endpoint.
8. Tests for all new routes.

**Frontend tasks:**
1. Client list page and new client form.
2. Client detail page with session history.
3. New audit session flow: select client → choose tier (core/extended) → start.
4. Field Companion UI (this is the most important UI in the app):
   - Room sections displayed as collapsible cards.
   - Each prompt shown one at a time within a section.
   - Text input with auto-save (debounce 2 seconds, save on blur).
   - Photo upload button on every prompt (camera and gallery options on mobile).
   - Skip button per prompt.
   - Progress bar showing completion across all sections.
   - Pause/resume: session state always in database, never in client storage.
   - Room order customizable (drag to reorder).
5. Observation review page: see all captured observations before advancing to diagnosis.
6. Mobile-first everything. Big tap targets, minimal scrolling to submit, fast load.

**Done when:**the practitioner can create a client, start a core audit session, walk through every room section on her phone entering observations and uploading photos, pause and resume the session, and review all captured observations before moving to diagnosis.

---

### Phase 3: Free-Form Capture (Mode 2)

**Goal:**the practitioner can dump observations in any format and the system categorizes them.

**Backend tasks:**
1. Categorization service using Claude Sonnet: send raw text + domain taxonomy → get room_area, category, domain_tags, confidence.
2. If confidence below threshold, return clarifying question instead of storing.
3. Free-form observation route that accepts text or photo, calls categorizer, stores result.
4. Tests for categorization accuracy.

**Frontend tasks:**
1. Free-form capture page within audit session: big text area, photo upload, submit.
2. After submit: show suggested categorization, letthe practitioner confirm or override.
3. If system returns clarifying question, display it and accept the practitioner's response.
4. All free-form observations visible alongside structured observations in the review page.

**Done when:**the practitioner can type or paste a quick observation, the system suggests the right room and category,the practitioner confirms, and it is saved to the session alongside structured observations.

---

### Phase 4: Diagnosis Engine and Report Generation

**Goal:** System generates scored reports from audit data using the RAG pipeline and Claude Opus. The practitioner reviews, overrides, and exports as PDF.

**Backend tasks:**
1. Alembic migration: add category_scores, reports, products, partners, report_product_refs, report_partner_refs tables.
2. Score generation service:
   - Group observations by category.
   - For each category, run hybrid RAG query across all 7 domains.
   - Build Claude Opus prompt with: category observations, retrieved knowledge, scoring criteria, the practitioner's voice guidelines.
   - Parse Claude response into: score, status_label, what_observed, why_it_matters, how_to_close_gap.
   - Match products and partners from the database.
   - Store all scores.
3. Report generation service:
   - Calculate overall score with the formula.
   - Generate Priority Action Plan (top 5 by lowest scores and highest leverage).
   - Generate "What Changes When You Fix This" section via Claude Opus with the practitioner's voice.
   - Generate Next Steps section.
   - Assemble full report.
4. Report PDF export:
   - HTML template with WellnessOps branding.
   - Score visualizations (CSS-based progress bars).
   - Photo thumbnails where observations included photos.
   - WeasyPrint HTML-to-PDF conversion.
5. Product and partner CRUD routes.
6. Report routes: generate, get, edit, approve, PDF export, preview.
7. Score override route with notes.
8. Tests for scoring pipeline, report generation, PDF export.

**Frontend tasks:**
1. Score review page: all category scores displayed as cards. Each shows AI score, status, observations summary. Override button on each with notes field.
2. Overall score display with qualitative label.
3. Report preview page: full report rendered in browser matching PDF layout.
4. Editable report sections:the practitioner can click into any section and edit text.
5. Approve button: locks report, triggers PDF generation.
6. PDF download button.
7. Report history: list of all reports for a session with version tracking.
8. Product management page: add/edit/deactivate vetted products.
9. Partner management page: add/edit/deactivate partners.

**Done when:**the practitioner can complete an audit, trigger score generation, review and override scores, preview the full report, edit sections, approve, and download a clean branded PDF.

---

### Phase 5: Pattern Recognition

**Goal:** System surfaces patterns from past audits when processing new clients.

**Backend tasks:**
1. Pattern extraction service: after audit completion, extract anonymized patterns from observations and scores.
2. Auto-populate Domain 4 (Client Patterns) in ChromaDB with extracted patterns.
3. Pattern matching on new intake: when generating scores for a new session, also query Domain 4 for similar patterns.
4. Include pattern matches in the diagnosis context sent to Claude Opus.
5. "Similar clients" endpoint: given a set of observations, return past pattern matches.

**Frontend tasks:**
1. During score review, show "Pattern matches" section under relevant categories.
2. Pattern matches display: what was observed in past clients, what the root cause turned out to be.

**Done when:** After 3+ audits, the system surfaces relevant patterns from past clients during new audit diagnosis.

---

### Phase 6: Partner Ecosystem and Polish

**Goal:** Reports automatically pull partner referrals. System is refined from real usage.

**Backend tasks:**
1. Auto-referral matching: based on category gaps, automatically suggest relevant partners.
2. Scoring calibration: track delta between AI scores andthe practitioner overrides, use to improve prompts.
3. Performance optimization: cache embedding model, optimize RAG queries, add database query optimization.

**Frontend tasks:**
1. Partner referral display in reports.
2. Dashboard improvements based on usage patterns.
3. Performance optimization: lazy loading, image optimization, service worker for offline field notes.

**Done when:** Reports include automatic partner referrals. Scoring accuracy has improved from calibration. The app is fast and polished.

---

## Critical Reminders

1. **Mobile-first.**the practitioner uses this on her phone in client homes. Every UI decision starts with the phone. Big tap targets, fast load, minimal scrolling.
2. **Knowledge base quality matters more than architecture.** A simple system fed the practitioner's specific knowledge produces something valuable. A perfect system fed generic content produces nothing.
3. **Low friction for adding knowledge.** If it is hard to add a document, it will not get updated. Make ingestion as simple as drag-and-drop or paste.
4. **The practitioner has final say on every score.** System generates, she approves. Never auto-publish.
5. **PDF must be clean and branded.** This is what clients see. It represents the practitioner's business.
6. **Enforce the Secure Build Standard.** Every route, every file upload, every log statement.
7. **Test as you build.** Each phase should have tests passing before moving to the next.
