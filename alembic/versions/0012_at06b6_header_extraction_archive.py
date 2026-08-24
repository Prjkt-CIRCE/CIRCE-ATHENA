"""AT-06B6 assisted header extraction and production archive.

Revision ID: 0012_at06b6_header_extraction_archive
Revises: 0011_at06b52_report_header
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_at06b6_header_extraction_archive"
down_revision = "0011_at06b52_report_header"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "report_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_key", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("shared_case_id", sa.Integer(), nullable=False),
        sa.Column("owner_username", sa.String(length=128), nullable=False),
        sa.Column("product_type", sa.String(length=128), nullable=False, server_default="RELATÓRIO TÉCNICO"),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("report_number", sa.String(length=128), nullable=True),
        sa.Column("report_date", sa.String(length=16), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["investigative_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_case_id"], ["shared_cases.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("product_key", name="uq_report_products_product_key"),
    )
    op.create_index("ix_report_products_product_key", "report_products", ["product_key"], unique=True)
    op.create_index("ix_report_products_workspace_id", "report_products", ["workspace_id"])
    op.create_index("ix_report_products_shared_case_id", "report_products", ["shared_case_id"])
    op.create_index("ix_report_products_owner_username", "report_products", ["owner_username"])
    op.create_index("ix_report_products_report_number", "report_products", ["report_number"])

    with op.batch_alter_table("workspace_report_headers") as batch:
        batch.add_column(sa.Column("report_product_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("review_status", sa.String(length=32), nullable=False, server_default="draft"))
        batch.add_column(sa.Column("confirmed_by_username", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key(
            "fk_workspace_report_headers_report_product_id",
            "report_products",
            ["report_product_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_workspace_report_headers_report_product_id", ["report_product_id"])

    op.create_table(
        "workspace_report_header_field_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_header_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("extracted_value", sa.Text(), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("source_label_snapshot", sa.String(length=512), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("extraction_method", sa.String(length=64), nullable=False, server_default="llm_pdf_text"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="proposed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_header_id"], ["workspace_report_headers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["shared_documents.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_workspace_report_header_field_sources_report_header_id",
        "workspace_report_header_field_sources",
        ["report_header_id"],
    )
    op.create_index(
        "ix_workspace_report_header_field_sources_field_name",
        "workspace_report_header_field_sources",
        ["field_name"],
    )
    op.create_index(
        "ix_workspace_report_header_field_sources_source_document_id",
        "workspace_report_header_field_sources",
        ["source_document_id"],
    )

    op.create_table(
        "report_metadata_index",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_product_id", sa.Integer(), nullable=False),
        sa.Column("key_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=False),
        sa.Column("source_scope", sa.String(length=64), nullable=False, server_default="case"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_product_id"], ["report_products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "report_product_id",
            "key_type",
            "normalized_value",
            name="uq_report_metadata_product_key_value",
        ),
    )
    op.create_index("ix_report_metadata_index_report_product_id", "report_metadata_index", ["report_product_id"])
    op.create_index("ix_report_metadata_index_key_type", "report_metadata_index", ["key_type"])


def downgrade() -> None:
    op.drop_index("ix_report_metadata_index_key_type", table_name="report_metadata_index")
    op.drop_index("ix_report_metadata_index_report_product_id", table_name="report_metadata_index")
    op.drop_table("report_metadata_index")

    op.drop_index(
        "ix_workspace_report_header_field_sources_source_document_id",
        table_name="workspace_report_header_field_sources",
    )
    op.drop_index(
        "ix_workspace_report_header_field_sources_field_name",
        table_name="workspace_report_header_field_sources",
    )
    op.drop_index(
        "ix_workspace_report_header_field_sources_report_header_id",
        table_name="workspace_report_header_field_sources",
    )
    op.drop_table("workspace_report_header_field_sources")

    with op.batch_alter_table("workspace_report_headers") as batch:
        batch.drop_index("ix_workspace_report_headers_report_product_id")
        batch.drop_constraint("fk_workspace_report_headers_report_product_id", type_="foreignkey")
        batch.drop_column("confirmed_at")
        batch.drop_column("confirmed_by_username")
        batch.drop_column("review_status")
        batch.drop_column("report_product_id")

    op.drop_index("ix_report_products_report_number", table_name="report_products")
    op.drop_index("ix_report_products_owner_username", table_name="report_products")
    op.drop_index("ix_report_products_shared_case_id", table_name="report_products")
    op.drop_index("ix_report_products_workspace_id", table_name="report_products")
    op.drop_index("ix_report_products_product_key", table_name="report_products")
    op.drop_table("report_products")
