"""Phase 2: clients, audit_sessions, observations tables

Revision ID: 002_phase2
Revises: 001_initial
Create Date: 2026-03-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_phase2"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(500), nullable=True),
        sa.Column("email", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(500), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("pii_consent", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("budget_tier", sa.String(50), nullable=True),
        sa.Column("has_wearable", sa.Boolean(), server_default="false"),
        sa.Column("wearable_type", sa.String(100), nullable=True),
        sa.Column("financial_audit_consent", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clients_user_id", "clients", ["user_id"])

    op.create_table(
        "audit_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("audit_tier", sa.String(20), server_default="core", nullable=False),
        sa.Column("status", sa.String(30), server_default="in_progress", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_sessions_client_id", "audit_sessions", ["client_id"])
    op.create_index("ix_audit_sessions_status", "audit_sessions", ["status"])

    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("audit_sessions.id"), nullable=False),
        sa.Column("room_area", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("observation_type", sa.String(30), server_default="text", nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("photo_path", sa.String(500), nullable=True),
        sa.Column("photo_thumbnail_path", sa.String(500), nullable=True),
        sa.Column("is_from_structured_flow", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("auto_categorized", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("domain_tags", sa.JSON(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("prompt_key", sa.String(100), nullable=True),
        sa.Column("skipped", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_observations_session_id", "observations", ["session_id"])
    op.create_index("ix_observations_room_area", "observations", ["room_area"])


def downgrade() -> None:
    op.drop_table("observations")
    op.drop_table("audit_sessions")
    op.drop_table("clients")
