"""0006 - reconcile AT-05 schema created previously by runtime bootstrap

Revision ID: 0006_at05_schema_reconciliation
Revises: 0005_platea
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_at05_schema_reconciliation"
down_revision = "0005_platea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "shared_case_annotations" not in tables:
        op.create_table(
            "shared_case_annotations",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "shared_case_id",
                sa.Integer,
                sa.ForeignKey("shared_cases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("created_by_operator_id", sa.Integer, nullable=True),
            sa.Column("created_by_username", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("source", sa.String(64), nullable=False),
        )
        op.create_index(
            "ix_shared_case_annotations_case",
            "shared_case_annotations",
            ["shared_case_id"],
        )

    if "assistant_execution_preferences" not in tables:
        op.create_table(
            "assistant_execution_preferences",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("operator_id", sa.Integer, nullable=False, unique=True),
            sa.Column("mode", sa.String(16), nullable=False, server_default="safe"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_assistant_execution_preferences_operator_id",
            "assistant_execution_preferences",
            ["operator_id"],
            unique=True,
        )


def downgrade() -> None:
    # No-op deliberado: estas tabelas podem ter sido criadas pelo bootstrap
    # legado antes desta migration. Removê-las poderia destruir dados AT-05.
    pass
