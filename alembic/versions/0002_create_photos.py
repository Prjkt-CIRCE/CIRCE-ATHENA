"""create photos table (AT-02)

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'photos',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nome_completo', sa.String(256), nullable=False),
        sa.Column('alcunhas', sa.Text(), nullable=True),
        sa.Column('cpf', sa.String(11), nullable=True),
        sa.Column('data_nascimento', sa.String(10), nullable=True),
        sa.Column('sexo', sa.String(32), nullable=False),
        sa.Column('etnia_cor', sa.String(32), nullable=False),
        sa.Column('estatura', sa.String(32), nullable=True),
        sa.Column('compleicao', sa.String(32), nullable=True),
        sa.Column('sinais_particulares', sa.Text(), nullable=True),
        sa.Column('organizacao_id', sa.Integer(), nullable=True),
        sa.Column('caso_vinculado', sa.String(256), nullable=True),
        sa.Column('contexto_foto', sa.String(64), nullable=False),
        sa.Column('fonte', sa.Text(), nullable=False),
        sa.Column('grau_confiabilidade', sa.String(16), nullable=False),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('caminho_foto', sa.String(512), nullable=False),
        sa.Column('sha256_foto', sa.String(64), nullable=False),
        sa.Column('embedding_path', sa.String(512), nullable=True),
        sa.Column('embedding_model', sa.String(128), nullable=True),
        sa.Column('embedding_extraido_em', sa.String(32), nullable=True),
        sa.Column('operador_id', sa.Integer(), nullable=False),
        sa.Column('operador_nome', sa.String(128), nullable=False),
        sa.Column('cadastrado_em', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_photos_nome_completo', 'photos', ['nome_completo'])
    op.create_index('ix_photos_sexo', 'photos', ['sexo'])
    op.create_index('ix_photos_etnia_cor', 'photos', ['etnia_cor'])
    op.create_index('ix_photos_grau_confiabilidade', 'photos', ['grau_confiabilidade'])
    op.create_index('ix_photos_operador_id', 'photos', ['operador_id'])
    op.create_index('ix_photos_sha256_foto', 'photos', ['sha256_foto'])


def downgrade() -> None:
    op.drop_index('ix_photos_sha256_foto', table_name='photos')
    op.drop_index('ix_photos_operador_id', table_name='photos')
    op.drop_index('ix_photos_grau_confiabilidade', table_name='photos')
    op.drop_index('ix_photos_etnia_cor', table_name='photos')
    op.drop_index('ix_photos_sexo', table_name='photos')
    op.drop_index('ix_photos_nome_completo', table_name='photos')
    op.drop_table('photos')