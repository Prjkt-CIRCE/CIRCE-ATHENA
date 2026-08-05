"""0005 - Platea: shared_cases, shared_persons, shared_documents, shared_links, platea_access_log

Revision ID: 0005_platea
Revises: 0004_photo_status_descarte
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_platea"
down_revision = "0004_photo_status_descarte"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shared_cases",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("case_ref", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("classification", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source_unit", sa.String(128), nullable=True),
        sa.Column("published_by", sa.String(128), nullable=False),
        sa.Column("published_at", sa.DateTime, nullable=False),
        sa.Column("published_version", sa.Integer, nullable=False, default=1),
        sa.Column("last_updated_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "shared_persons",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("shared_case_id", sa.Integer, sa.ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_ref", sa.String(64), nullable=True),
        sa.Column("full_name", sa.String(256), nullable=False),
        sa.Column("aliases", sa.Text, nullable=True),
        sa.Column("cpf", sa.String(16), nullable=True),
        sa.Column("rg", sa.String(32), nullable=True),
        sa.Column("birth_date", sa.String(16), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("reliability_level", sa.String(32), nullable=True),
        sa.Column("role_in_case", sa.String(64), nullable=True),
    )
    op.create_index("ix_shared_persons_case", "shared_persons", ["shared_case_id"])

    op.create_table(
        "shared_documents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("shared_case_id", sa.Integer, sa.ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_ref", sa.String(64), nullable=True),
        sa.Column("filename", sa.String(256), nullable=False),
        sa.Column("file_type", sa.String(32), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("imported_at", sa.String(32), nullable=True),
    )
    op.create_index("ix_shared_documents_case", "shared_documents", ["shared_case_id"])

    op.create_table(
        "shared_links",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("shared_case_id", sa.Integer, sa.ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_type", sa.String(32), nullable=False),
        sa.Column("entity_a_ref", sa.String(64), nullable=False),
        sa.Column("entity_a_name", sa.String(256), nullable=True),
        sa.Column("entity_b_ref", sa.String(64), nullable=False),
        sa.Column("entity_b_name", sa.String(256), nullable=True),
        sa.Column("link_nature", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_shared_links_case", "shared_links", ["shared_case_id"])

    op.create_table(
        "platea_access_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("shared_case_id", sa.Integer, sa.ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_ref", sa.String(64), nullable=False),
        sa.Column("operator_id", sa.Integer, nullable=False),
        sa.Column("operator_login", sa.String(128), nullable=False),
        sa.Column("accessed_at", sa.DateTime, nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
    )
    op.create_index("ix_platea_access_case", "platea_access_log", ["shared_case_id"])
    op.create_index("ix_platea_access_operator", "platea_access_log", ["operator_id"])


def downgrade() -> None:
    op.drop_table("platea_access_log")
    op.drop_table("shared_links")
    op.drop_table("shared_documents")
    op.drop_table("shared_persons")
    op.drop_table("shared_cases")