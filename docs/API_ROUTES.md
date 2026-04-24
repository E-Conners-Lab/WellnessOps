# API Routes — WellnessOps

## Base URL

`/api/v1`

All routes require authentication unless marked PUBLIC. Authentication via JWT access token in httpOnly cookie (SEC-01). Authorization checked on every data operation (SEC-03).

---

## Auth

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | /auth/login | Login, returns JWT pair | PUBLIC |
| POST | /auth/logout | Invalidate session | Required |
| POST | /auth/refresh | Rotate refresh token (SEC-16) | Refresh token |

## Health

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | /health | Service health check | PUBLIC |
| GET | /health/db | Database connectivity | PUBLIC |
| GET | /health/chroma | ChromaDB connectivity | PUBLIC |

## Clients

| Method | Path | Description |
|---|---|---|
| GET | /clients | List all clients for authenticated user |
| POST | /clients | Create new client profile |
| GET | /clients/{id} | Get client details |
| PUT | /clients/{id} | Update client profile |
| DELETE | /clients/{id} | Soft delete client |
| GET | /clients/{id}/sessions | List audit sessions for client |
| POST | /clients/{id}/export | Export all client data (data portability) |

## Audit Sessions

| Method | Path | Description |
|---|---|---|
| POST | /audits | Start new audit session (linked to client) |
| GET | /audits/{id} | Get audit session with observations |
| PUT | /audits/{id} | Update session metadata (tier, status, notes) |
| PUT | /audits/{id}/status | Advance session status |
| GET | /audits/{id}/progress | Get completion progress by room/section |

## Observations

| Method | Path | Description |
|---|---|---|
| POST | /audits/{id}/observations | Add observation (text, photo, measurement) |
| PUT | /observations/{id} | Edit observation |
| DELETE | /observations/{id} | Delete observation |
| POST | /audits/{id}/observations/bulk | Bulk add observations (for structured flow completion) |
| POST | /observations/categorize | Auto-categorize free-form input via Claude Sonnet |

## File Uploads

| Method | Path | Description |
|---|---|---|
| POST | /uploads/photo | Upload photo, strip EXIF, return path (SEC-21, SEC-22) |
| POST | /uploads/document | Upload document for knowledge ingestion |
| GET | /uploads/{path} | Retrieve file via signed URL (SEC-20) |

## Scores

| Method | Path | Description |
|---|---|---|
| GET | /audits/{id}/scores | Get all category scores for session |
| POST | /audits/{id}/scores/generate | Trigger AI score generation |
| PUT | /scores/{id} | Override individual score (practitioner override) |
| PUT | /scores/{id}/override | Mark score as practitioner-overridden with notes |

## Reports

| Method | Path | Description |
|---|---|---|
| POST | /audits/{id}/reports/generate | Generate report from session data + RAG |
| GET | /reports/{id} | Get report content |
| PUT | /reports/{id} | Edit report sections |
| PUT | /reports/{id}/approve | Approve report (practitioner sign-off) |
| GET | /reports/{id}/pdf | Download PDF export |
| GET | /reports/{id}/preview | Preview report as rendered HTML |

## Knowledge Base

| Method | Path | Description |
|---|---|---|
| GET | /knowledge/documents | List all ingested documents with filters |
| POST | /knowledge/documents | Upload and ingest new document |
| GET | /knowledge/documents/{id} | Get document metadata and chunk preview |
| DELETE | /knowledge/documents/{id} | Remove document and its chunks from ChromaDB |
| GET | /knowledge/domains | List domain stats (doc count, chunk count per domain) |
| POST | /knowledge/search | Search across domains (for testing retrieval) |

## Products

| Method | Path | Description |
|---|---|---|
| GET | /products | List all products with filters (category, recommended) |
| POST | /products | Add new vetted product |
| PUT | /products/{id} | Update product |
| DELETE | /products/{id} | Deactivate product |

## Partners

| Method | Path | Description |
|---|---|---|
| GET | /partners | List all partners with filters (category, location) |
| POST | /partners | Add new partner |
| PUT | /partners/{id} | Update partner |
| DELETE | /partners/{id} | Deactivate partner |

---

## Standard Response Format

```json
{
    "status": "success",
    "data": { ... },
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 45
    }
}
```

## Error Response Format (SEC-11)

```json
{
    "status": "error",
    "message": "Human-readable error message",
    "correlation_id": "uuid-for-log-lookup"
}
```

Never expose stack traces, internal paths, or database errors in production responses.
