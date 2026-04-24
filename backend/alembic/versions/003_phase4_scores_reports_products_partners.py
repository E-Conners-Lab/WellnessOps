"""Phase 4: category_scores, reports, products, partners, junction tables

Revision ID: 003_phase4
Revises: 002_phase2
Create Date: 2026-03-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_phase4"
down_revision: Union[str, None] = "002_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "category_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("audit_sessions.id"), nullable=False),
        sa.Column("category_key", sa.String(100), nullable=False),
        sa.Column("category_name", sa.String(255), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("ai_generated_score", sa.Integer(), nullable=True),
        sa.Column("status_label", sa.String(50), nullable=False),
        sa.Column("what_observed", sa.Text(), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("how_to_close_gap", sa.Text(), nullable=True),
        sa.Column("is_extended_category", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("practitioner_override", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("override_notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "category_key", name="uq_session_category"),
    )
    op.create_index("ix_category_scores_session_id", "category_scores", ["session_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("audit_sessions.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("overall_label", sa.String(50), nullable=False),
        sa.Column("priority_action_plan", sa.JSON(), nullable=True),
        sa.Column("vision_section", sa.Text(), nullable=True),
        sa.Column("next_steps", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("generated_by", sa.String(50), nullable=False, server_default="system"),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "version", name="uq_session_version"),
    )
    op.create_index("ix_reports_session_id", "reports", ["session_id"])

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("price_range", sa.String(50), nullable=True),
        sa.Column("purchase_link", sa.Text(), nullable=True),
        sa.Column("why_recommended", sa.Text(), nullable=False),
        sa.Column("best_for", sa.Text(), nullable=True),
        sa.Column("contraindications", sa.Text(), nullable=True),
        sa.Column("practitioner_note", sa.Text(), nullable=True),
        sa.Column("is_recommended", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("not_recommended_reason", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_category", "products", ["category"])

    op.create_table(
        "partners",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("why_recommended", sa.Text(), nullable=False),
        sa.Column("best_for_client_type", sa.Text(), nullable=True),
        sa.Column("pricing_tier", sa.String(50), nullable=True),
        sa.Column("is_ambassador", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("practitioner_note", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_partners_category", "partners", ["category"])

    op.create_table(
        "report_product_refs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("category_key", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id", "product_id", name="uq_report_product"),
    )

    op.create_table(
        "report_partner_refs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("partner_id", sa.Uuid(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("category_key", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id", "partner_id", name="uq_report_partner"),
    )


def downgrade() -> None:
    op.drop_table("report_partner_refs")
    op.drop_table("report_product_refs")
    op.drop_table("partners")
    op.drop_table("products")
    op.drop_table("reports")
    op.drop_table("category_scores")
