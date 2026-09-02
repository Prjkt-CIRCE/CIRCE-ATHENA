"""UX-03A persistent Product and Sections foundation.

Revision ID: 0010_ux03a_product_sections
Revises: 0009_at06b_curated_intake_storage
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_ux03a_product_sections"
down_revision = "0009_at06b_curated_intake_storage"
branch_labels = None
depends_on = None


NEW_TABLES = {
    "workspace_products",
    "workspace_product_sections",
    "workspace_product_section_blocks",
}


def upgrade() -> None:
    existing = NEW_TABLES.intersection(sa.inspect(op.get_bind()).get_table_names())
    if existing:
        raise RuntimeError(
            "UX-03A migration found pre-existing target table(s): " + ", ".join(sorted(existing))
        )

    op.create_table(
        "workspace_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("investigative_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by_operator_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(length=128), nullable=False),
        sa.Column("updated_by_operator_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_username", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision >= 1", name="ck_workspace_products_revision_positive"),
    )
    op.create_index("ix_workspace_products_workspace_id", "workspace_products", ["workspace_id"])

    op.create_table(
        "workspace_product_sections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("workspace_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_by_operator_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(length=128), nullable=False),
        sa.Column("updated_by_operator_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_username", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_workspace_product_sections_position_nonnegative"),
        sa.UniqueConstraint("product_id", "position", name="uq_workspace_product_section_position"),
    )
    op.create_index("ix_workspace_product_sections_product_id", "workspace_product_sections", ["product_id"])

    op.create_table(
        "workspace_product_section_blocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("section_id", sa.Integer(), sa.ForeignKey("workspace_product_sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_id", sa.Integer(), sa.ForeignKey("investigative_blocks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_by_operator_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_workspace_product_section_blocks_position_nonnegative"),
        sa.UniqueConstraint("section_id", "block_id", name="uq_workspace_product_section_block"),
        sa.UniqueConstraint("section_id", "position", name="uq_workspace_product_section_block_position"),
    )
    op.create_index("ix_workspace_product_section_blocks_section_id", "workspace_product_section_blocks", ["section_id"])
    op.create_index("ix_workspace_product_section_blocks_block_id", "workspace_product_section_blocks", ["block_id"])


def downgrade() -> None:
    op.drop_table("workspace_product_section_blocks")
    op.drop_table("workspace_product_sections")
    op.drop_table("workspace_products")
