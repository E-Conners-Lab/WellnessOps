# Database Schema — WellnessOps

## Overview

PostgreSQL 16 with async access via SQLAlchemy 2.0 + asyncpg. All tables use UUID primary keys. Timestamps are UTC. Soft deletes where appropriate (is_deleted flag + deleted_at).

---

## Core Tables

### users

The practitioner (and future team members). Auth target.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Argon2id (SEC-17)
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'practitioner',  -- practitioner, admin
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### clients

Client profiles with anonymization support. PII stored only with consent flag.

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),          -- practitioner who owns this client
    display_name VARCHAR(255) NOT NULL,                   -- can be anonymized code
    full_name VARCHAR(255),                               -- PII, nullable
    email VARCHAR(255),                                   -- PII, nullable
    phone VARCHAR(50),                                    -- PII, nullable
    address TEXT,                                         -- PII, nullable
    pii_consent BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    budget_tier VARCHAR(50),                              -- budget, moderate, premium
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

Individual audit engagements linked to a client.

```sql
CREATE TABLE audit_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    user_id UUID NOT NULL REFERENCES users(id),
    audit_tier VARCHAR(20) NOT NULL DEFAULT 'core',      -- core, extended
    status VARCHAR(30) NOT NULL DEFAULT 'in_progress',   -- in_progress, observations_complete, diagnosis_pending, report_draft, report_final, closed
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_sessions_client_id ON audit_sessions(client_id);
CREATE INDEX idx_audit_sessions_status ON audit_sessions(status);
```

### observations

Individual observations within an audit session. Supports text, photos, and structured data.

```sql
CREATE TABLE observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES audit_sessions(id),
    room_area VARCHAR(100) NOT NULL,                     -- entry, living, kitchen, bedroom, workspace, hidden_spaces, vehicle, wearable, financial, client_responses
    category VARCHAR(100),                                -- maps to scoring categories
    observation_type VARCHAR(30) NOT NULL DEFAULT 'text', -- text, photo, measurement, wearable_data
    content TEXT,                                          -- text observation or structured JSON
    photo_path VARCHAR(500),                              -- relative path to stored photo
    photo_thumbnail_path VARCHAR(500),
    is_from_structured_flow BOOLEAN NOT NULL DEFAULT true, -- true = Field Companion, false = Free-Form
    auto_categorized BOOLEAN NOT NULL DEFAULT false,       -- true if categorized by Claude
    domain_tags VARCHAR(50)[],                             -- which knowledge domains are relevant
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_observations_session_id ON observations(session_id);
CREATE INDEX idx_observations_room_area ON observations(room_area);
```

### category_scores

Scores per category per audit session. Supportsthe practitioner override.

```sql
CREATE TABLE category_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES audit_sessions(id),
    category_key VARCHAR(100) NOT NULL,                   -- setup_vs_goals, intention, hidden_spaces, kitchen, etc.
    category_name VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 10),
    ai_generated_score INTEGER,                           -- what the system suggested before override
    status_label VARCHAR(50) NOT NULL,                    -- Exceptional, Strong, Adequate, Problematic, etc.
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

CREATE INDEX idx_category_scores_session_id ON category_scores(session_id);
```

### reports

Generated reports with versioning.

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES audit_sessions(id),
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',          -- draft, review, final
    overall_score INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    overall_label VARCHAR(50) NOT NULL,
    priority_action_plan JSONB,                            -- top 5 actions as structured JSON
    vision_section TEXT,                                    -- "What Changes When You Fix This"
    next_steps TEXT,
    pdf_path VARCHAR(500),
    generated_by VARCHAR(50) NOT NULL DEFAULT 'system',    -- system, manual
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, version)
);

CREATE INDEX idx_reports_session_id ON reports(session_id);
```

### products

Vetted product catalog. Mirrored from ChromaDB Domain 3.

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(100) NOT NULL,                       -- air_quality, sleep, lighting, food, movement, hydration, supplements, organization, sensory, ergonomics, biophilic
    price_range VARCHAR(50),
    purchase_link TEXT,
    why_recommended TEXT NOT NULL,
    best_for TEXT,
    contraindications TEXT,
    practitioner_note TEXT,
    is_recommended BOOLEAN NOT NULL DEFAULT true,          -- false = "do not recommend" list
    not_recommended_reason TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_is_recommended ON products(is_recommended);
```

### partners

Partner and vendor directory. Mirrored from ChromaDB Domain 7.

```sql
CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255),
    category VARCHAR(100) NOT NULL,                       -- organizer, chef, trainer, therapist, skincare, acupuncture, functional_medicine, sleep_specialist, ergonomics, cleaning, plants, lighting, smart_home, etc.
    location VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    website VARCHAR(500),
    why_recommended TEXT NOT NULL,
    best_for_client_type TEXT,
    pricing_tier VARCHAR(50),                             -- budget, moderate, premium
    is_ambassador BOOLEAN NOT NULL DEFAULT false,
    practitioner_note TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_partners_category ON partners(category);
```

### knowledge_documents

Metadata for all documents ingested into ChromaDB.

```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,                          -- well, research, products, patterns, philosophies, aesthetics, partners
    title VARCHAR(500) NOT NULL,
    source VARCHAR(500),                                   -- URL, book title, the practitioner's notes, etc.
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    tags VARCHAR(100)[],
    chunk_count INTEGER NOT NULL DEFAULT 0,
    chromadb_collection VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ,
    ingestion_status VARCHAR(30) NOT NULL DEFAULT 'pending', -- pending, processing, complete, failed
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_knowledge_documents_domain ON knowledge_documents(domain);
CREATE INDEX idx_knowledge_documents_tags ON knowledge_documents USING GIN(tags);
```

### report_product_refs

Junction table linking reports to recommended products.

```sql
CREATE TABLE report_product_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id),
    product_id UUID NOT NULL REFERENCES products(id),
    category_key VARCHAR(100),                            -- which audit category triggered this recommendation
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE(report_id, product_id)
);
```

### report_partner_refs

Junction table linking reports to recommended partners.

```sql
CREATE TABLE report_partner_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id),
    partner_id UUID NOT NULL REFERENCES partners(id),
    category_key VARCHAR(100),
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE(report_id, partner_id)
);
```

### audit_log

Immutable audit trail (SEC-28). Write-only from application.

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,                          -- login, logout, client_create, client_view, observation_create, report_generate, report_export, knowledge_ingest, etc.
    resource_type VARCHAR(100),                             -- client, audit_session, observation, report, product, partner, knowledge_document
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

## Migration Strategy

Use Alembic for database migrations. Each phase adds its tables incrementally.

- Phase 1: users, knowledge_documents, audit_log
- Phase 2: clients, audit_sessions, observations
- Phase 3: (no new tables, uses existing observations)
- Phase 4: category_scores, reports, products, partners, report_product_refs, report_partner_refs
