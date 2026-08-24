from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InvestigativeWorkspace(Base):
    __tablename__ = "investigative_workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shared_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    blocks: Mapped[List["InvestigativeBlock"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="InvestigativeBlock.created_at",
    )
    excerpts: Mapped[List["InvestigativeExcerpt"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="InvestigativeExcerpt.created_at",
    )
    findings: Mapped[List["InvestigativeFinding"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="InvestigativeFinding.created_at",
    )
    work_topics: Mapped[List["InvestigativeWorkTopic"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="InvestigativeWorkTopic.position",
    )


class InvestigativeBlock(Base):
    __tablename__ = "investigative_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="working", nullable=False)
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    authorship_mode: Mapped[str] = mapped_column(String(32), default="literal", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    workspace: Mapped["InvestigativeWorkspace"] = relationship(back_populates="blocks")
    sources: Mapped[List["InvestigativeBlockSource"]] = relationship(
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="InvestigativeBlockSource.position",
    )


class InvestigativeBlockSource(Base):
    __tablename__ = "investigative_block_sources"
    __table_args__ = (
        UniqueConstraint("block_id", "source_type", "source_key", name="uq_block_source_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_key: Mapped[str] = mapped_column(String(256), nullable=False)
    source_label_snapshot: Mapped[str] = mapped_column(String(512), nullable=False)
    source_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relation: Mapped[str] = mapped_column(String(32), default="context", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    block: Mapped["InvestigativeBlock"] = relationship(back_populates="sources")


# AT06B2_WORK_TOPICS_V1
class InvestigativeWorkTopic(Base):
    __tablename__ = "investigative_work_topics"
    __table_args__ = (
        UniqueConstraint("workspace_id", "topic_key", name="uq_workspace_topic_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_topic_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("investigative_work_topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    topic_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topic_type: Mapped[str] = mapped_column(String(64), default="narrative", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped["InvestigativeWorkspace"] = relationship(back_populates="work_topics")
    parent: Mapped[Optional["InvestigativeWorkTopic"]] = relationship(remote_side="InvestigativeWorkTopic.id")
    excerpts: Mapped[List["InvestigativeExcerpt"]] = relationship(back_populates="work_topic")
    findings: Mapped[List["InvestigativeFinding"]] = relationship(back_populates="work_topic")


# AT06B1_ANALYTICAL_CORE_V1
class InvestigativeExcerpt(Base):
    __tablename__ = "investigative_excerpts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_topic_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("investigative_work_topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    analyst_note: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_summary: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_type: Mapped[str] = mapped_column(String(32), default="annotation", nullable=False)
    support_gaps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    workspace: Mapped["InvestigativeWorkspace"] = relationship(back_populates="excerpts")
    work_topic: Mapped[Optional["InvestigativeWorkTopic"]] = relationship(back_populates="excerpts")
    sources: Mapped[List["InvestigativeExcerptSource"]] = relationship(
        back_populates="excerpt",
        cascade="all, delete-orphan",
        order_by="InvestigativeExcerptSource.position",
    )
    finding: Mapped[Optional["InvestigativeFinding"]] = relationship(
        back_populates="excerpt",
        uselist=False,
    )


class InvestigativeExcerptSource(Base):
    __tablename__ = "investigative_excerpt_sources"
    __table_args__ = (
        UniqueConstraint("excerpt_id", "source_type", "source_key", name="uq_excerpt_source_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    excerpt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_excerpts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_key: Mapped[str] = mapped_column(String(256), nullable=False)
    source_label_snapshot: Mapped[str] = mapped_column(String(512), nullable=False)
    source_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    excerpt: Mapped["InvestigativeExcerpt"] = relationship(back_populates="sources")


class InvestigativeFinding(Base):
    __tablename__ = "investigative_findings"
    __table_args__ = (
        UniqueConstraint("excerpt_id", name="uq_finding_excerpt"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_topic_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("investigative_work_topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    excerpt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_excerpts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    objective_summary: Mapped[str] = mapped_column(Text, nullable=False)
    interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finding_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="validated", nullable=False)
    authorship_mode: Mapped[str] = mapped_column(String(32), default="assisted_drafting", nullable=False)
    validated_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    validated_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    workspace: Mapped["InvestigativeWorkspace"] = relationship(back_populates="findings")
    work_topic: Mapped[Optional["InvestigativeWorkTopic"]] = relationship(back_populates="findings")
    excerpt: Mapped["InvestigativeExcerpt"] = relationship(back_populates="finding")
