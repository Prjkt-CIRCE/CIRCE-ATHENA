"""AT-06B6.3 factual map and narrative topic composition.

Revision ID: 0013_at06b63_facts_topic_composition
Revises: 0012_at06b6_header_extraction_archive
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0013_at06b63_facts_topic_composition"
down_revision = "0012_at06b6_header_extraction_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_topic_compositions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("work_topic_id", sa.Integer(), nullable=False),
        sa.Column("analyst_context", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("confirmed_by_username", sa.String(length=128), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by_username", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["investigative_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_topic_id"], ["investigative_work_topics.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("work_topic_id", name="uq_workspace_topic_composition_topic"),
    )
    op.create_index("ix_workspace_topic_compositions_workspace_id", "workspace_topic_compositions", ["workspace_id"])
    op.create_index("ix_workspace_topic_compositions_work_topic_id", "workspace_topic_compositions", ["work_topic_id"])

    op.create_table(
        "workspace_topic_composition_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("composition_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_key", sa.String(length=256), nullable=False),
        sa.Column("source_label_snapshot", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["composition_id"], ["workspace_topic_compositions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("composition_id", "source_type", "source_key", name="uq_topic_composition_source_identity"),
    )
    op.create_index("ix_workspace_topic_composition_sources_composition_id", "workspace_topic_composition_sources", ["composition_id"])

    op.create_table(
        "workspace_topic_facts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("composition_id", sa.Integer(), nullable=False),
        sa.Column("fact_key", sa.String(length=96), nullable=False),
        sa.Column("label", sa.String(length=256), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="proposed"),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("source_label_snapshot", sa.String(length=512), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["composition_id"], ["workspace_topic_compositions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["shared_documents.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("composition_id", "fact_key", name="uq_topic_fact_key"),
    )
    op.create_index("ix_workspace_topic_facts_composition_id", "workspace_topic_facts", ["composition_id"])
    op.create_index("ix_workspace_topic_facts_source_document_id", "workspace_topic_facts", ["source_document_id"])

    op.create_table(
        "workspace_topic_narrative_blocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("composition_id", sa.Integer(), nullable=False),
        sa.Column("block_key", sa.String(length=96), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("authorship_mode", sa.String(length=32), nullable=False, server_default="assisted_drafting"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["composition_id"], ["workspace_topic_compositions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("composition_id", "block_key", name="uq_topic_narrative_block_key"),
    )
    op.create_index("ix_workspace_topic_narrative_blocks_composition_id", "workspace_topic_narrative_blocks", ["composition_id"])

    op.create_table(
        "workspace_topic_narrative_block_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("narrative_block_id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("source_label_snapshot", sa.String(length=512), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["narrative_block_id"], ["workspace_topic_narrative_blocks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["shared_documents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_workspace_topic_narrative_block_sources_block_id", "workspace_topic_narrative_block_sources", ["narrative_block_id"])
    op.create_index("ix_workspace_topic_narrative_block_sources_document_id", "workspace_topic_narrative_block_sources", ["source_document_id"])


def downgrade() -> None:
    op.drop_index("ix_workspace_topic_narrative_block_sources_document_id", table_name="workspace_topic_narrative_block_sources")
    op.drop_index("ix_workspace_topic_narrative_block_sources_block_id", table_name="workspace_topic_narrative_block_sources")
    op.drop_table("workspace_topic_narrative_block_sources")
    op.drop_index("ix_workspace_topic_narrative_blocks_composition_id", table_name="workspace_topic_narrative_blocks")
    op.drop_table("workspace_topic_narrative_blocks")
    op.drop_index("ix_workspace_topic_facts_source_document_id", table_name="workspace_topic_facts")
    op.drop_index("ix_workspace_topic_facts_composition_id", table_name="workspace_topic_facts")
    op.drop_table("workspace_topic_facts")
    op.drop_index("ix_workspace_topic_composition_sources_composition_id", table_name="workspace_topic_composition_sources")
    op.drop_table("workspace_topic_composition_sources")
    op.drop_index("ix_workspace_topic_compositions_work_topic_id", table_name="workspace_topic_compositions")
    op.drop_index("ix_workspace_topic_compositions_workspace_id", table_name="workspace_topic_compositions")
    op.drop_table("workspace_topic_compositions")
