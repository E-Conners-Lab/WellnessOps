# WellnessOps — System Plan

The high-level system specification. Implementation details live in `CLAUDE_CODE_HANDOFF.md`. Per-area docs live in this folder.

## Purpose

A mobile-first audit platform for wellness practitioners conducting in-home client assessments. The system supports structured and free-form observation capture, retrieves grounded knowledge from a curated multi-domain corpus, generates scored reports with the practitioner reviewing and overriding before final delivery, and exports branded PDFs.

## Knowledge domains (7)

The RAG corpus is organized into seven domains, each a separate ChromaDB collection. Documents in each domain are chunked, embedded, and indexed independently.

1. **Environment** — air, water, light, temperature, sound, EMF, and other environmental inputs
2. **Research** — peer-reviewed studies and evidence base supporting recommendations
3. **Products** — vetted products with usage notes and best-fit criteria
4. **Patterns** — recurring observation patterns across client engagements
5. **Philosophies** — frameworks and methodologies underpinning the audit approach
6. **Aesthetics** — design principles for biophilic and intentional space design
7. **Partners** — referral network of complementary practitioners

## Interaction modes

### Mode 1 — Field Companion (structured)
Room-by-room guided prompts. Each prompt accepts text, photo, or skip. Used in client homes when the practitioner wants thorough coverage. Prompts live in `docs/FIELD_COMPANION_PROMPTS.md`.

### Mode 2 — Free-Form Capture
Practitioner dumps observations in any format (text, voice transcribed). Claude Sonnet auto-categorizes each observation into the right room/category, with practitioner confirmation before save.

### Mode 3 — Diagnosis & Report Review
After capture, the diagnosis engine retrieves grounded context from all 7 domains, scores 10 categories on a 100-point scale, and drafts a full client report. Practitioner reviews, overrides any score with notes (preserved for calibration tracking), edits any section, and approves for PDF export.

## Scoring framework

10 categories scored 1-10, weighted to a 100-point composite. See `docs/SCORING_METHODOLOGY.md` for criteria and weighting. Each score includes:
- The score itself
- An `ai_generated_score` snapshot (preserved even when overridden)
- A `practitioner_override` flag and notes
- A `what_observed` explanation
- A `why_it_matters` justification (grounded in retrieved knowledge)
- A `how_to_close_gap` recommendation

## Report structure

See `docs/REPORT_STRUCTURE.md` for the complete report template, including: vision section, scored category breakdown, prioritized actions, vetted products, partner referrals, next steps.

## Audit session lifecycle

```
in_progress → observations_complete → diagnosis_pending →
report_draft → report_final → closed
```

State transitions are explicit; the system never auto-publishes.

## Voice and tone

Reports are written in the practitioner's voice. The system generates a draft; the practitioner edits before sending. The diagnosis engine prompt is tuned to match the practitioner's tone profile (curious, direct, non-judgmental, evidence-anchored).

## Non-goals

- Not a medical diagnosis tool. Recommendations are environmental and lifestyle, not clinical.
- Not a fully autonomous system. The practitioner has final say on every score and every recommendation.
- Not a marketplace. Product and partner suggestions are advisory.

## Architecture summary

See the top-level [README](../README.md) for the architecture diagram, tech stack, and RAG pipeline details.
