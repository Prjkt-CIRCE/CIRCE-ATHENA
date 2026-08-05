"""AT-02c: campos status e descarte logico na tabela photos

Revision ID: 0004_photo_status_descarte
Revises: 0003_batch_import_fields
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_photo_status_descarte"
down_revision = "0003_batch_import_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "photos",
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="ativo",
        ),
    )
    op.add_column(
        "photos",
        sa.Column("motivo_descarte", sa.Text(), nullable=True),
    )
    op.add_column(
        "photos",
        sa.Column("descartado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "photos",
        sa.Column("descartado_por", sa.String(128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("photos", "descartado_por")
    op.drop_column("photos", "descartado_em")
    op.drop_column("photos", "motivo_descarte")
    op.drop_column("photos", "status")