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
