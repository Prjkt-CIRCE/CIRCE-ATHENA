"""CURATED-00 - repair reproducible foundation tables.

Revision ID: 0008_curated_foundation_repair
Revises: 0007_at06a_workspace_core
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_curated_foundation_repair"
down_revision = "0007_at06a_workspace_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "operators" not in tables:
        op.create_table(
            "operators",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("username", sa.String(length=64), nullable=False, unique=True),
            sa.Column("full_name", sa.String(length=128), nullable=False),
            sa.Column("password_hash", sa.String(length=256), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("failed_attempts", sa.Integer(), nullable=False),
            sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        )

    tables = set(sa.inspect(bind).get_table_names())
    if "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("operator_id", sa.Integer(), nullable=True),
            sa.Column("operator_username", sa.String(length=64), nullable=True),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=True),
            sa.Column("entity_id", sa.String(length=64), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("ip_address", sa.String(length=64), nullable=True),
            sa.Column("previous_hash", sa.String(length=64), nullable=False),
            sa.Column("current_hash", sa.String(length=64), nullable=False),
        )

    tables = set(sa.inspect(bind).get_table_names())
    if "sync_queue" not in tables:
        op.create_table(
            "sync_queue",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("source_system", sa.String(length=64), nullable=False),
            sa.Column("payload_type", sa.String(length=64), nullable=False),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    # Non-destructive on purpose: these foundational tables may predate Alembic.
    pass
