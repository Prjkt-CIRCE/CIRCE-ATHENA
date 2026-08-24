from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReportHeaderTemplate(Base):
    __tablename__ = "report_header_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    state_name: Mapped[str] = mapped_column(String(256), nullable=False)
    secretariat_name: Mapped[str] = mapped_column(String(256), nullable=False)
    agency_name: Mapped[str] = mapped_column(String(256), nullable=False)
    directorate_name: Mapped[str] = mapped_column(String(256), nullable=False)
    police_unit_name: Mapped[str] = mapped_column(String(512), nullable=False)
    section_name: Mapped[str] = mapped_column(String(256), nullable=False)
    report_label: Mapped[str] = mapped_column(String(128), nullable=False, default="RELATÓRIO TÉCNICO")

    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class ReportProduct(Base):
    """Produto persistente no acervo de produção do policial.

    O produto nasce antes da exportação DOCX/PDF. Isso permite que metadados,
    autoria e contexto continuem pesquisáveis anos depois.
    """

    __tablename__ = "report_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shared_case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shared_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_username: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    product_type: Mapped[str] = mapped_column(String(128), nullable=False, default="RELATÓRIO TÉCNICO")
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    report_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    report_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_entries: Mapped[List["ReportMetadataIndex"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ReportMetadataIndex.id",
    )


class ReportMetadataIndex(Base):
    __tablename__ = "report_metadata_index"
    __table_args__ = (
        UniqueConstraint(
            "report_product_id",
            "key_type",
            "normalized_value",
            name="uq_report_metadata_product_key_value",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("report_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="case")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    product: Mapped["ReportProduct"] = relationship(back_populates="metadata_entries")


class WorkspaceReportHeader(Base):
    __tablename__ = "workspace_report_headers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("report_header_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("report_products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    state_name: Mapped[str] = mapped_column(String(256), nullable=False)
    secretariat_name: Mapped[str] = mapped_column(String(256), nullable=False)
    agency_name: Mapped[str] = mapped_column(String(256), nullable=False)
    directorate_name: Mapped[str] = mapped_column(String(256), nullable=False)
    police_unit_name: Mapped[str] = mapped_column(String(512), nullable=False)
    section_name: Mapped[str] = mapped_column(String(256), nullable=False)
    report_label: Mapped[str] = mapped_column(String(128), nullable=False, default="RELATÓRIO TÉCNICO")

    report_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    report_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    distribution: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    previous_distribution: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    references_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    annexes_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    confirmed_by_username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    template: Mapped[Optional["ReportHeaderTemplate"]] = relationship()
    report_product: Mapped[Optional["ReportProduct"]] = relationship()
    sources: Mapped[List["WorkspaceReportHeaderSource"]] = relationship(
        back_populates="header",
        cascade="all, delete-orphan",
        order_by="WorkspaceReportHeaderSource.id",
    )
    field_sources: Mapped[List["WorkspaceReportHeaderFieldSource"]] = relationship(
        back_populates="header",
        cascade="all, delete-orphan",
        order_by="WorkspaceReportHeaderFieldSource.id",
    )


class WorkspaceReportHeaderSource(Base):
    __tablename__ = "workspace_report_header_sources"
    __table_args__ = (
        UniqueConstraint(
            "report_header_id",
            "source_type",
            "source_key",
            name="uq_report_header_source_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_header_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_report_headers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_key: Mapped[str] = mapped_column(String(256), nullable=False)
    source_label_snapshot: Mapped[str] = mapped_column(String(512), nullable=False)

    header: Mapped["WorkspaceReportHeader"] = relationship(back_populates="sources")


class WorkspaceReportHeaderFieldSource(Base):
    """Proveniência de uma proposta de campo do cabeçalho."""

    __tablename__ = "workspace_report_header_field_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_header_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_report_headers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    extracted_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_document_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("shared_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_label_snapshot: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False, default="llm_pdf_text")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    header: Mapped["WorkspaceReportHeader"] = relationship(back_populates="field_sources")


# AT06B63_TOPIC_COMPOSITION_V1
class WorkspaceTopicComposition(Base):
    """Composição persistente de um Tópico narrativo do relatório."""

    __tablename__ = "workspace_topic_compositions"
    __table_args__ = (
        UniqueConstraint("work_topic_id", name="uq_workspace_topic_composition_topic"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_topic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigative_work_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analyst_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    confirmed_by_username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    sources: Mapped[List["WorkspaceTopicCompositionSource"]] = relationship(
        back_populates="composition",
        cascade="all, delete-orphan",
        order_by="WorkspaceTopicCompositionSource.id",
    )
    facts: Mapped[List["WorkspaceTopicFact"]] = relationship(
        back_populates="composition",
        cascade="all, delete-orphan",
        order_by="WorkspaceTopicFact.position",
    )
    narrative_blocks: Mapped[List["WorkspaceTopicNarrativeBlock"]] = relationship(
        back_populates="composition",
        cascade="all, delete-orphan",
        order_by="WorkspaceTopicNarrativeBlock.position",
    )


class WorkspaceTopicCompositionSource(Base):
    __tablename__ = "workspace_topic_composition_sources"
    __table_args__ = (
        UniqueConstraint(
            "composition_id", "source_type", "source_key",
            name="uq_topic_composition_source_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    composition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_topic_compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_key: Mapped[str] = mapped_column(String(256), nullable=False)
    source_label_snapshot: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    composition: Mapped["WorkspaceTopicComposition"] = relationship(back_populates="sources")


class WorkspaceTopicFact(Base):
    __tablename__ = "workspace_topic_facts"
    __table_args__ = (
        UniqueConstraint("composition_id", "fact_key", name="uq_topic_fact_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    composition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_topic_compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fact_key: Mapped[str] = mapped_column(String(96), nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    source_document_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("shared_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_label_snapshot: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    composition: Mapped["WorkspaceTopicComposition"] = relationship(back_populates="facts")


class WorkspaceTopicNarrativeBlock(Base):
    __tablename__ = "workspace_topic_narrative_blocks"
    __table_args__ = (
        UniqueConstraint("composition_id", "block_key", name="uq_topic_narrative_block_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    composition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_topic_compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    block_key: Mapped[str] = mapped_column(String(96), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    authorship_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="assisted_drafting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    composition: Mapped["WorkspaceTopicComposition"] = relationship(back_populates="narrative_blocks")
    sources: Mapped[List["WorkspaceTopicNarrativeBlockSource"]] = relationship(
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="WorkspaceTopicNarrativeBlockSource.id",
    )


class WorkspaceTopicNarrativeBlockSource(Base):
    __tablename__ = "workspace_topic_narrative_block_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    narrative_block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_topic_narrative_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_document_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("shared_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_label_snapshot: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    block: Mapped["WorkspaceTopicNarrativeBlock"] = relationship(back_populates="sources")
