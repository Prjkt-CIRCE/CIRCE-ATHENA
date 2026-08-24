"""0008 - AT-06B1 Núcleo de Análise Investigativa

Revision ID: 0008_at06b1_analytical_core
Revises: 0007_at06a_workspace_core
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_at06b1_analytical_core"
down_revision = "0007_at06a_workspace_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "investigative_excerpts" not in tables:
        op.create_table(
            "investigative_excerpts",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "workspace_id",
                sa.Integer,
                sa.ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("analyst_note", sa.Text, nullable=False),
            sa.Column("proposed_summary", sa.Text, nullable=False),
            sa.Column("proposed_interpretation", sa.Text, nullable=True),
            sa.Column("suggested_type", sa.String(32), nullable=False, server_default="annotation"),
            sa.Column("support_gaps", sa.Text, nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
            sa.Column("created_by_operator_id", sa.Integer, nullable=True),
            sa.Column("created_by_username", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_investigative_excerpts_workspace_id",
            "investigative_excerpts",
            ["workspace_id"],
        )

    tables = set(sa.inspect(bind).get_table_names())
    if "investigative_excerpt_sources" not in tables:
        op.create_table(
            "investigative_excerpt_sources",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "excerpt_id",
                sa.Integer,
                sa.ForeignKey("investigative_excerpts.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("source_type", sa.String(32), nullable=False),
            sa.Column("source_key", sa.String(256), nullable=False),
            sa.Column("source_label_snapshot", sa.String(512), nullable=False),
            sa.Column("source_snapshot", sa.Text, nullable=True),
            sa.Column("position", sa.Integer, nullable=False, server_default="0"),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "excerpt_id",
                "source_type",
                "source_key",
                name="uq_excerpt_source_identity",
            ),
        )
        op.create_index(
            "ix_investigative_excerpt_sources_excerpt_id",
            "investigative_excerpt_sources",
            ["excerpt_id"],
        )

    tables = set(sa.inspect(bind).get_table_names())
    if "investigative_findings" not in tables:
        op.create_table(
            "investigative_findings",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "workspace_id",
                sa.Integer,
                sa.ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "excerpt_id",
                sa.Integer,
                sa.ForeignKey("investigative_excerpts.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("objective_summary", sa.Text, nullable=False),
            sa.Column("interpretation", sa.Text, nullable=True),
            sa.Column("finding_type", sa.String(32), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="validated"),
            sa.Column("authorship_mode", sa.String(32), nullable=False, server_default="assisted_drafting"),
            sa.Column("validated_by_operator_id", sa.Integer, nullable=True),
            sa.Column("validated_by_username", sa.String(128), nullable=False),
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("excerpt_id", name="uq_finding_excerpt"),
        )
        op.create_index(
            "ix_investigative_findings_workspace_id",
            "investigative_findings",
            ["workspace_id"],
        )
        op.create_index(
            "ix_investigative_findings_excerpt_id",
            "investigative_findings",
            ["excerpt_id"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_table("investigative_findings")
    op.drop_table("investigative_excerpt_sources")
    op.drop_table("investigative_excerpts")
