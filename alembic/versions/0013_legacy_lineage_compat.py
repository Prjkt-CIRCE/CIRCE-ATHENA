"""Compatibility bridge for the legacy AT-06B63 Alembic lineage.

Revision ID: 0013_at06b63_facts_topic_composition
Revises: 0008_curated_foundation_repair
Create Date: 2026-08-25

This revision intentionally does not recreate the retired AT-06B63 report/topic
schema. Its purpose is to reconnect databases already stamped with the legacy
0013 revision to the current CURATED migration lineage.

Fresh CURATED databases reaching this revision are validated for the minimum
canonical schema required by the current application.
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_at06b63_facts_topic_composition"
down_revision = "0008_curated_foundation_repair"
branch_labels = None
depends_on = None


REQUIRED_TABLES = {
    "operators",
    "audit_logs",
    "sync_queue",
    "shared_cases",
    "shared_persons",
    "shared_documents",
    "shared_links",
    "shared_case_annotations",
    "investigative_workspaces",
    "investigative_blocks",
    "investigative_block_sources",
}


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    missing = sorted(REQUIRED_TABLES - tables)

    if missing:
        raise RuntimeError(
            "Legacy-lineage compatibility gate failed. "
            "Missing required tables: "
            + ", ".join(missing)
        )

    # No destructive DDL here.
    # Legacy-only tables are intentionally preserved.


def downgrade() -> None:
    # Compatibility marker only. Never remove legacy data/tables here.
    pass
