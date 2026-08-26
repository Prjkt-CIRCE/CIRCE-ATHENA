"""AT-06B-CURATED-01 - canonical physical storage metadata.

Revision ID: 0009_at06b_curated_intake_storage
Revises: 0013_at06b63_facts_topic_composition
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_at06b_curated_intake_storage"
down_revision = "0013_at06b63_facts_topic_composition"
branch_labels = None
depends_on = None


def _column_names(bind) -> set[str]:
    return {
        item["name"]
        for item in sa.inspect(bind).get_columns("shared_documents")
    }


def _index_names(bind) -> set[str]:
    return {
        item["name"]
        for item in sa.inspect(bind).get_indexes("shared_documents")
        if item.get("name")
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "shared_documents" not in tables:
        raise RuntimeError(
            "shared_documents não existe; "
            "AT-06B-CURATED-01 não pode ser aplicada."
        )

    columns = _column_names(bind)

    if "storage_relpath" not in columns:
        op.add_column(
            "shared_documents",
            sa.Column(
                "storage_relpath",
                sa.String(length=1024),
                nullable=True,
            ),
        )

    if "mime_type" not in columns:
        op.add_column(
            "shared_documents",
            sa.Column(
                "mime_type",
                sa.String(length=128),
                nullable=True,
            ),
        )

    if "size_bytes" not in columns:
        op.add_column(
            "shared_documents",
            sa.Column(
                "size_bytes",
                sa.Integer(),
                nullable=True,
            ),
        )

    if "storage_origin" not in columns:
        op.add_column(
            "shared_documents",
            sa.Column(
                "storage_origin",
                sa.String(length=64),
                nullable=True,
            ),
        )

    if "stored_at" not in columns:
        op.add_column(
            "shared_documents",
            sa.Column(
                "stored_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

    indexes = _index_names(bind)

    if "ix_shared_documents_case_sha256" not in indexes:
        op.create_index(
            "ix_shared_documents_case_sha256",
            "shared_documents",
            ["shared_case_id", "sha256"],
            unique=False,
        )

    if "ux_shared_documents_storage_relpath" not in indexes:
        op.create_index(
            "ux_shared_documents_storage_relpath",
            "shared_documents",
            ["storage_relpath"],
            unique=True,
        )


def downgrade() -> None:
    # Deliberately non-destructive.
    #
    # This migration supports two historical lineages. In particular,
    # mime_type already exists in legacy AT-06B63 databases, so removing
    # columns during downgrade could destroy pre-existing schema/data.
    pass
