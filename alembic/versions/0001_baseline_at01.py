"""baseline AT-01: registra tabelas existentes sem recriar

Revision ID: 0001
Revises: 
Create Date: 2026-08-04
"""
from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tabelas operators, audit_logs e sync_queue ja existem no banco.
    # Esta migracao serve apenas como baseline de historico.
    pass


def downgrade() -> None:
    pass