"""0007 - AT-06A Workspace Investigativo core

Revision ID: 0007_at06a_workspace_core
Revises: 0006_at05_schema_reconciliation
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_at06a_workspace_core"
down_revision = "0006_at05_schema_reconciliation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "investigative_workspaces" not in tables:
        op.create_table(
            "investigative_workspaces",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "shared_case_id",
                sa.Integer,
                sa.ForeignKey("shared_cases.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("created_by_operator_id", sa.Integer, nullable=True),
            sa.Column("created_by_username", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_investigative_workspaces_shared_case_id",
            "investigative_workspaces",
            ["shared_case_id"],
            unique=True,
        )

    tables = set(sa.inspect(bind).get_table_names())
    if "investigative_blocks" not in tables:
        op.create_table(
            "investigative_blocks",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "workspace_id",
                sa.Integer,
                sa.ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("summary", sa.Text, nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="working"),
            sa.Column("created_by_operator_id", sa.Integer, nullable=True),
            sa.Column("created_by_username", sa.String(128), nullable=False),
            sa.Column("authorship_mode", sa.String(32), nullable=False, server_default="literal"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_investigative_blocks_workspace_id",
            "investigative_blocks",
            ["workspace_id"],
        )

    tables = set(sa.inspect(bind).get_table_names())
    if "investigative_block_sources" not in tables:
        op.create_table(
            "investigative_block_sources",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "block_id",
                sa.Integer,
                sa.ForeignKey("investigative_blocks.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("source_type", sa.String(32), nullable=False),
            sa.Column("source_key", sa.String(256), nullable=False),
            sa.Column("source_label_snapshot", sa.String(512), nullable=False),
            sa.Column("source_snapshot", sa.Text, nullable=True),
            sa.Column("relation", sa.String(32), nullable=False, server_default="context"),
            sa.Column("position", sa.Integer, nullable=False, server_default="0"),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "block_id",
                "source_type",
                "source_key",
                name="uq_block_source_identity",
            ),
        )
        op.create_index(
            "ix_investigative_block_sources_block_id",
            "investigative_block_sources",
            ["block_id"],
        )


def downgrade() -> None:
    op.drop_table("investigative_block_sources")
    op.drop_table("investigative_blocks")
    op.drop_table("investigative_workspaces")
