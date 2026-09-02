from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceProduct(Base):
    __tablename__ = "workspace_products"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_workspace_products_revision_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    updated_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    sections: Mapped[List["ProductSection"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by=lambda: (ProductSection.position, ProductSection.id),
    )


class ProductSection(Base):
    __tablename__ = "workspace_product_sections"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_workspace_product_sections_position_nonnegative"),
        UniqueConstraint("product_id", "position", name="uq_workspace_product_section_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    updated_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    product: Mapped[WorkspaceProduct] = relationship(back_populates="sections")
    block_links: Mapped[List["ProductSectionBlock"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        order_by=lambda: (ProductSectionBlock.position, ProductSectionBlock.id),
    )


class ProductSectionBlock(Base):
    __tablename__ = "workspace_product_section_blocks"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_workspace_product_section_blocks_position_nonnegative"),
        UniqueConstraint("section_id", "block_id", name="uq_workspace_product_section_block"),
        UniqueConstraint("section_id", "position", name="uq_workspace_product_section_block_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_product_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_blocks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    section: Mapped[ProductSection] = relationship(back_populates="block_links")
    block = relationship("InvestigativeBlock")
