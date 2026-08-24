"""AT-06B2 work topics and topic-aware analytical core.

Revision ID: 0009_at06b2_work_topics
Revises: 0008_at06b1_analytical_core
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_at06b2_work_topics"
down_revision = "0008_at06b1_analytical_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigative_work_topics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("parent_topic_id", sa.Integer(), nullable=True),
        sa.Column("topic_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("topic_type", sa.String(length=64), nullable=False, server_default="narrative"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_operator_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["investigative_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_topic_id"], ["investigative_work_topics.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("workspace_id", "topic_key", name="uq_workspace_topic_key"),
    )
    op.create_index("ix_investigative_work_topics_workspace_id", "investigative_work_topics", ["workspace_id"])
    op.create_index("ix_investigative_work_topics_parent_topic_id", "investigative_work_topics", ["parent_topic_id"])

    with op.batch_alter_table("investigative_excerpts") as batch:
        batch.add_column(sa.Column("work_topic_id", sa.Integer(), nullable=True))
        batch.create_index("ix_investigative_excerpts_work_topic_id", ["work_topic_id"])
        batch.create_foreign_key(
            "fk_investigative_excerpts_work_topic_id",
            "investigative_work_topics",
            ["work_topic_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("investigative_findings") as batch:
        batch.add_column(sa.Column("work_topic_id", sa.Integer(), nullable=True))
        batch.create_index("ix_investigative_findings_work_topic_id", ["work_topic_id"])
        batch.create_foreign_key(
            "fk_investigative_findings_work_topic_id",
            "investigative_work_topics",
            ["work_topic_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("investigative_findings") as batch:
        batch.drop_constraint("fk_investigative_findings_work_topic_id", type_="foreignkey")
        batch.drop_index("ix_investigative_findings_work_topic_id")
        batch.drop_column("work_topic_id")

    with op.batch_alter_table("investigative_excerpts") as batch:
        batch.drop_constraint("fk_investigative_excerpts_work_topic_id", type_="foreignkey")
        batch.drop_index("ix_investigative_excerpts_work_topic_id")
        batch.drop_column("work_topic_id")

    op.drop_index("ix_investigative_work_topics_parent_topic_id", table_name="investigative_work_topics")
    op.drop_index("ix_investigative_work_topics_workspace_id", table_name="investigative_work_topics")
    op.drop_table("investigative_work_topics")
