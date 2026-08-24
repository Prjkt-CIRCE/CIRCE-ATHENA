"""AT-06B5 native case creation and initial intake metadata.

Revision ID: 0010_at06b5_native_case_intake
Revises: 0009_at06b2_work_topics
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0010_at06b5_native_case_intake"
down_revision = "0009_at06b2_work_topics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("shared_cases") as batch:
        batch.add_column(sa.Column("case_uuid", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("origin_type", sa.String(length=32), nullable=False, server_default="external_sync"))
        batch.add_column(sa.Column("created_by_operator_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("created_by_username", sa.String(length=128), nullable=True))
        batch.create_index("ix_shared_cases_case_uuid", ["case_uuid"], unique=True)

    with op.batch_alter_table("shared_documents") as batch:
        batch.add_column(sa.Column("storage_path", sa.String(length=512), nullable=True))
        batch.add_column(sa.Column("mime_type", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("file_size", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("intake_bin", sa.String(length=64), nullable=False, server_default="documents"))
        batch.add_column(sa.Column("origin", sa.String(length=64), nullable=False, server_default="external_sync"))
        batch.add_column(sa.Column("uploaded_by_username", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_shared_documents_intake_bin", ["intake_bin"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("shared_documents") as batch:
        batch.drop_index("ix_shared_documents_intake_bin")
        batch.drop_column("uploaded_at")
        batch.drop_column("uploaded_by_username")
        batch.drop_column("origin")
        batch.drop_column("intake_bin")
        batch.drop_column("file_size")
        batch.drop_column("mime_type")
        batch.drop_column("storage_path")

    with op.batch_alter_table("shared_cases") as batch:
        batch.drop_index("ix_shared_cases_case_uuid")
        batch.drop_column("created_by_username")
        batch.drop_column("created_by_operator_id")
        batch.drop_column("origin_type")
        batch.drop_column("case_uuid")
