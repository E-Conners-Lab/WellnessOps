"""
Report generation service.
Assembles scored data into a complete client report.
Generates vision section and next steps via LLM.
Exports to PDF via WeasyPrint.
"""

import os
import uuid as uuid_mod
from datetime import datetime, timezone

import structlog
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.audit import AuditSession
from app.db.models.client import Client
from app.db.models.report import Report
from app.db.models.score import CategoryScore, get_overall_label
from app.services.llm import chat_completion

logger = structlog.stdlib.get_logger()

VISION_SYSTEM_PROMPT = """You are a wellness practitioner. Write the "What Changes When You Fix This" section of a client's wellness audit report.

Paint a vivid, warm picture of what daily life looks and feels like AFTER the client implements the top recommendations. Be specific to their situation. Not clinical. Not overwhelming. Make them feel like change is not only possible but exciting.

Write 2-3 short paragraphs. Use "you" language. No bullet points in this section -- it should read like a letter from a trusted friend who happens to be an expert."""

NEXT_STEPS_SYSTEM_PROMPT = """You are a wellness practitioner. Write the "Next Steps" section of a client's wellness audit report.

Give clear, actionable instructions on:
1. What to tackle first (the highest-impact, lowest-effort change)
2. What to tackle in week 2-3
3. When to consider professional help (partner referral)
4. How to reachthe practitioner for implementation support

Keep it to 4-5 numbered steps. Direct and specific, not generic. Reference their actual scores and observations."""


async def generate_report(
    db: AsyncSession,
    session_id: str | uuid_mod.UUID,
    user_id: str | uuid_mod.UUID,
) -> Report:
    """Generate a complete report from scored audit data.

    1. Calculate overall score
    2. Generate priority action plan
    3. Generate vision section via LLM
    4. Generate next steps via LLM
    5. Assemble and store report
    """
    if isinstance(session_id, str):
        session_id = uuid_mod.UUID(session_id)

    # Get scores
    result = await db.execute(
        select(CategoryScore)
        .where(CategoryScore.session_id == session_id)
        .order_by(CategoryScore.sort_order)
    )
    scores = result.scalars().all()

    if not scores:
        raise ValueError("No scores found. Generate scores before creating a report.")

    # Calculate overall score
    applicable_scores = [s for s in scores if s.score > 0]
    if applicable_scores:
        total = sum(s.score for s in applicable_scores)
        overall = round((total / (len(applicable_scores) * 10)) * 100)
    else:
        overall = 0

    overall_label = get_overall_label(overall)

    # Priority action plan: top 5 lowest-scoring categories
    sorted_scores = sorted(applicable_scores, key=lambda s: s.score)
    action_plan = {
        "actions": [
            {
                "rank": i + 1,
                "category_key": s.category_key,
                "category_name": s.category_name,
                "score": s.score,
                "action": s.how_to_close_gap or "Review and address gaps in this area.",
            }
            for i, s in enumerate(sorted_scores[:5])
        ]
    }

    # Auto-referral matching (Phase 6)
    referrals = {"product_matches": {}, "partner_matches": {}}
    try:
        from app.services.referral_matcher import match_referrals
        referrals = await match_referrals(db, scores)
    except Exception:
        logger.exception("referral_matching_failed")

    action_plan["referrals"] = referrals

    # Build context for LLM sections
    score_summary = "\n".join(
        f"- {s.category_name}: {s.score}/10 ({s.status_label})"
        for s in scores
    )
    observations_summary = "\n".join(
        f"- {s.category_name}: {s.what_observed}"
        for s in scores
        if s.what_observed
    )
    top_actions = "\n".join(
        f"{a['rank']}. {a['category_name']} ({a['score']}/10): {a['action']}"
        for a in action_plan["actions"]
    )

    context = f"""Overall score: {overall}/100 ({overall_label})

Category scores:
{score_summary}

Key observations:
{observations_summary}

Top 5 priority actions:
{top_actions}"""

    # Generate vision section
    try:
        vision = await chat_completion(
            system=VISION_SYSTEM_PROMPT,
            user_message=f"Write the vision section for this client:\n\n{context}",
            max_tokens=500,
            model_tier="reasoning",
        )
    except Exception:
        logger.exception("vision_generation_failed")
        vision = "Vision section generation failed. Please write this section manually."

    # Generate next steps
    try:
        next_steps = await chat_completion(
            system=NEXT_STEPS_SYSTEM_PROMPT,
            user_message=f"Write the next steps for this client:\n\n{context}",
            max_tokens=400,
            model_tier="reasoning",
        )
    except Exception:
        logger.exception("next_steps_generation_failed")
        next_steps = "Next steps generation failed. Please write this section manually."

    # Determine version
    version_result = await db.execute(
        select(func.coalesce(func.max(Report.version), 0))
        .where(Report.session_id == session_id)
    )
    next_version = version_result.scalar() + 1

    report = Report(
        session_id=session_id,
        version=next_version,
        status="draft",
        overall_score=overall,
        overall_label=overall_label,
        priority_action_plan=action_plan,
        vision_section=vision,
        next_steps=next_steps,
        generated_by="system",
    )
    db.add(report)
    await db.flush()

    logger.info(
        "report_generated",
        session_id=session_id,
        version=next_version,
        overall_score=overall,
    )

    return report


async def generate_pdf(
    db: AsyncSession,
    report: Report,
    session_id: str,
) -> str:
    """Generate a branded PDF from the report data.

    Returns the relative file path to the generated PDF.
    """
    # Get session and client info
    session_result = await db.execute(
        select(AuditSession).where(AuditSession.id == session_id)
    )
    session = session_result.scalar_one()

    client_result = await db.execute(
        select(Client).where(Client.id == session.client_id)
    )
    client = client_result.scalar_one()

    # Get scores
    scores_result = await db.execute(
        select(CategoryScore)
        .where(CategoryScore.session_id == session_id)
        .order_by(CategoryScore.sort_order)
    )
    scores = scores_result.scalars().all()

    # Render HTML template
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "reports")
    os.makedirs(template_dir, exist_ok=True)

    env = Environment(loader=FileSystemLoader(template_dir))

    # Create template if it doesn't exist
    template_path = os.path.join(template_dir, "client_report.html")
    if not os.path.exists(template_path):
        _create_default_template(template_path)

    template = env.get_template("client_report.html")
    html = template.render(
        client_name=client.display_name,
        audit_date=session.started_at.strftime("%B %d, %Y"),
        audit_tier=session.audit_tier.title(),
        overall_score=report.overall_score,
        overall_label=report.overall_label,
        scores=scores,
        priority_actions=report.priority_action_plan.get("actions", []) if report.priority_action_plan else [],
        vision_section=report.vision_section,
        next_steps=report.next_steps,
        report_version=report.version,
        generated_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
    )

    # Generate PDF with WeasyPrint
    from weasyprint import HTML

    pdf_dir = os.path.join(settings.upload_dir, "reports")
    os.makedirs(pdf_dir, exist_ok=True)

    date_str = session.started_at.strftime("%Y-%m-%d")
    safe_name = client.display_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_Wellness_Audit_{date_str}_v{report.version}.pdf"
    pdf_path = os.path.join(pdf_dir, filename)

    HTML(string=html).write_pdf(pdf_path)

    rel_path = f"reports/{filename}"
    report.pdf_path = rel_path
    await db.flush()

    logger.info("pdf_generated", path=rel_path)
    return rel_path


def _create_default_template(path: str) -> None:
    """Create the default report HTML template."""
    template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page { size: letter; margin: 1in; }
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; font-size: 11pt; }
  h1 { color: #166534; font-size: 24pt; margin-bottom: 0.2em; }
  h2 { color: #166534; font-size: 16pt; border-bottom: 2px solid #dcfce7; padding-bottom: 0.3em; margin-top: 1.5em; }
  h3 { color: #15803d; font-size: 13pt; margin-top: 1em; }
  .header { text-align: center; margin-bottom: 2em; border-bottom: 3px solid #166534; padding-bottom: 1em; }
  .header .brand { font-size: 10pt; color: #6b7280; letter-spacing: 2px; text-transform: uppercase; }
  .header .client { font-size: 20pt; color: #166534; margin: 0.3em 0; }
  .header .meta { font-size: 9pt; color: #9ca3af; }
  .overall-score { text-align: center; margin: 2em 0; padding: 1.5em; background: #f0fdf4; border-radius: 12px; }
  .overall-score .number { font-size: 48pt; font-weight: bold; color: #166534; }
  .overall-score .label { font-size: 16pt; color: #15803d; }
  .category { margin-bottom: 1.5em; padding: 1em; border: 1px solid #e5e7eb; border-radius: 8px; page-break-inside: avoid; }
  .category .score-bar { height: 8px; background: #e5e7eb; border-radius: 4px; margin: 0.5em 0; }
  .category .score-fill { height: 100%; border-radius: 4px; }
  .category .score-fill.high { background: #22c55e; }
  .category .score-fill.mid { background: #f59e0b; }
  .category .score-fill.low { background: #ef4444; }
  .category .detail { font-size: 10pt; color: #4b5563; margin: 0.5em 0; }
  .category .detail strong { color: #1a1a1a; }
  .action-item { margin: 0.5em 0; padding: 0.5em; background: #fffbeb; border-left: 3px solid #f59e0b; }
  .vision { background: #f0fdf4; padding: 1.5em; border-radius: 8px; margin: 1em 0; font-style: italic; }
  .footer { text-align: center; font-size: 8pt; color: #9ca3af; margin-top: 2em; border-top: 1px solid #e5e7eb; padding-top: 0.5em; }
</style>
</head>
<body>

<div class="header">
  <div class="brand">WellnessOps</div>
  <div class="client">{{ client_name }}</div>
  <div class="meta">{{ audit_tier }} Audit -- {{ audit_date }}</div>
  <div class="meta">Practitioner: a wellness practitioner</div>
</div>

<div class="overall-score">
  <div class="number">{{ overall_score }}</div>
  <div class="label">{{ overall_label }}</div>
  <div style="font-size: 10pt; color: #6b7280; margin-top: 0.5em;">out of 100</div>
</div>

<h2>Category Scores</h2>
{% for score in scores %}
<div class="category">
  <h3>{{ score.category_name }} -- {{ score.score }}/10 ({{ score.status_label }})</h3>
  <div class="score-bar">
    <div class="score-fill {% if score.score >= 7 %}high{% elif score.score >= 4 %}mid{% else %}low{% endif %}"
         style="width: {{ score.score * 10 }}%"></div>
  </div>
  {% if score.what_observed %}
  <div class="detail"><strong>What I observed:</strong> {{ score.what_observed }}</div>
  {% endif %}
  {% if score.why_it_matters %}
  <div class="detail"><strong>Why it matters:</strong> {{ score.why_it_matters }}</div>
  {% endif %}
  {% if score.how_to_close_gap %}
  <div class="detail"><strong>How to close the gap:</strong> {{ score.how_to_close_gap }}</div>
  {% endif %}
  {% if score.practitioner_override %}
  <div class="detail" style="color: #7c3aed;"><strong>the practitioner's note:</strong> {{ score.override_notes }}</div>
  {% endif %}
</div>
{% endfor %}

<h2>Priority Action Plan</h2>
{% for action in priority_actions %}
<div class="action-item">
  <strong>{{ action.rank }}. {{ action.category_name }}</strong> ({{ action.score }}/10)<br>
  {{ action.action }}
</div>
{% endfor %}

{% if vision_section %}
<h2>What Changes When You Fix This</h2>
<div class="vision">{{ vision_section }}</div>
{% endif %}

{% if next_steps %}
<h2>Next Steps</h2>
<div style="white-space: pre-wrap;">{{ next_steps }}</div>
{% endif %}

<div class="footer">
  WellnessOps -- {{ client_name }} -- {{ audit_tier }} Audit -- {{ generated_date }} -- Version {{ report_version }}
</div>

</body>
</html>"""
    with open(path, "w") as f:
        f.write(template)
