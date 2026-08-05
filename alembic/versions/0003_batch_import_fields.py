"""AT-02b: campos importado_em_lote e revisado_em na tabela photos

Revision ID: 0003_batch_import_fields
Revises: 0002
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_batch_import_fields"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "photos",
        sa.Column(
            "importado_em_lote",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "photos",
        sa.Column(
            "revisado_em",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("photos", "revisado_em")
    op.drop_column("photos", "importado_em_lote")