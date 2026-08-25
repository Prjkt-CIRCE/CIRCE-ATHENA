"""AT-06B-CURATED-01 - canonical physical storage metadata.

Revision ID: 0009_at06b_curated_intake_storage
Revises: 0008_curated_foundation_repair
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_at06b_curated_intake_storage"
down_revision = "0008_curated_foundation_repair"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shared_documents",
        sa.Column("storage_relpath", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "shared_documents",
        sa.Column("mime_type", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "shared_documents",
        sa.Column("size_bytes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "shared_documents",
        sa.Column("storage_origin", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "shared_documents",
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_shared_documents_case_sha256",
        "shared_documents",
        ["shared_case_id", "sha256"],
        unique=False,
    )
    op.create_index(
        "ux_shared_documents_storage_relpath",
        "shared_documents",
        ["storage_relpath"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_shared_documents_storage_relpath",
        table_name="shared_documents",
    )
    op.drop_index(
        "ix_shared_documents_case_sha256",
        table_name="shared_documents",
    )

    op.drop_column("shared_documents", "stored_at")
    op.drop_column("shared_documents", "storage_origin")
    op.drop_column("shared_documents", "size_bytes")
    op.drop_column("shared_documents", "mime_type")
    op.drop_column("shared_documents", "storage_relpath")
