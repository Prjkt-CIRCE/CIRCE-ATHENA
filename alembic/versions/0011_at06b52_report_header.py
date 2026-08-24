"""AT-06B5.2 report header template and workspace header.

Revision ID: 0011_at06b52_report_header
Revises: 0010_at06b5_native_case_intake
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0011_at06b52_report_header"
down_revision = "0010_at06b5_native_case_intake"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE shared_documents
        SET intake_bin = 'documents',
            description = 'Material recebido no Pool do caso; classificação semântica e extração ainda pendentes.'
        WHERE origin = 'native_intake'
          AND intake_bin = 'inbox'
        """
    )

    op.create_table(
        "report_header_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("state_name", sa.String(length=256), nullable=False),
        sa.Column("secretariat_name", sa.String(length=256), nullable=False),
        sa.Column("agency_name", sa.String(length=256), nullable=False),
        sa.Column("directorate_name", sa.String(length=256), nullable=False),
        sa.Column("police_unit_name", sa.String(length=512), nullable=False),
        sa.Column("section_name", sa.String(length=256), nullable=False),
        sa.Column("report_label", sa.String(length=128), nullable=False, server_default="RELATÓRIO TÉCNICO"),
        sa.Column("created_by_username", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "workspace_report_headers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("state_name", sa.String(length=256), nullable=False),
        sa.Column("secretariat_name", sa.String(length=256), nullable=False),
        sa.Column("agency_name", sa.String(length=256), nullable=False),
        sa.Column("directorate_name", sa.String(length=256), nullable=False),
        sa.Column("police_unit_name", sa.String(length=512), nullable=False),
        sa.Column("section_name", sa.String(length=256), nullable=False),
        sa.Column("report_label", sa.String(length=128), nullable=False, server_default="RELATÓRIO TÉCNICO"),
        sa.Column("report_number", sa.String(length=128), nullable=True),
        sa.Column("report_date", sa.String(length=16), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("origin", sa.String(length=512), nullable=True),
        sa.Column("distribution", sa.String(length=512), nullable=True),
        sa.Column("previous_distribution", sa.String(length=512), nullable=True),
        sa.Column("references_text", sa.Text(), nullable=True),
        sa.Column("annexes_text", sa.Text(), nullable=True),
        sa.Column("updated_by_username", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["investigative_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["report_header_templates.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("workspace_id", name="uq_workspace_report_header_workspace"),
    )
    op.create_index("ix_workspace_report_headers_workspace_id", "workspace_report_headers", ["workspace_id"])
    op.create_index("ix_workspace_report_headers_template_id", "workspace_report_headers", ["template_id"])

    op.create_table(
        "workspace_report_header_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_header_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_key", sa.String(length=256), nullable=False),
        sa.Column("source_label_snapshot", sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(["report_header_id"], ["workspace_report_headers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "report_header_id",
            "source_type",
            "source_key",
            name="uq_report_header_source_identity",
        ),
    )
    op.create_index(
        "ix_workspace_report_header_sources_report_header_id",
        "workspace_report_header_sources",
        ["report_header_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workspace_report_header_sources_report_header_id",
        table_name="workspace_report_header_sources",
    )
    op.drop_table("workspace_report_header_sources")

    op.drop_index("ix_workspace_report_headers_template_id", table_name="workspace_report_headers")
    op.drop_index("ix_workspace_report_headers_workspace_id", table_name="workspace_report_headers")
    op.drop_table("workspace_report_headers")

    op.drop_table("report_header_templates")
