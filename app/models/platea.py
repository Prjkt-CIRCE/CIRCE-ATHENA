"""
Modelos SQLAlchemy — Platea (AT-03)
Tabelas: shared_cases, shared_persons, shared_documents, shared_links, platea_access_log
Padrao: Mapped/mapped_column, Base importada de app.database
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SharedCase(Base):
    __tablename__ = "shared_cases"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_ref:          Mapped[str]           = mapped_column(String(64),  nullable=False, unique=True)
    title:             Mapped[str]           = mapped_column(String(256), nullable=False)
    status:            Mapped[str]           = mapped_column(String(32),  nullable=False)
    classification:    Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)
    notes:             Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    source_unit:       Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    published_by:      Mapped[str]           = mapped_column(String(128), nullable=False)
    published_at:      Mapped[datetime]      = mapped_column(DateTime,    nullable=False)
    published_version: Mapped[int]           = mapped_column(Integer,     nullable=False, default=1)
    last_updated_at:   Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    persons:   Mapped[List["SharedPerson"]]    = relationship(back_populates="case", cascade="all, delete-orphan")
    documents: Mapped[List["SharedDocument"]]  = relationship(back_populates="case", cascade="all, delete-orphan")
    links:     Mapped[List["SharedLink"]]      = relationship(back_populates="case", cascade="all, delete-orphan")
    accesses:  Mapped[List["PlateaAccessLog"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    annotations: Mapped[List["SharedCaseAnnotation"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class SharedPerson(Base):
    __tablename__ = "shared_persons"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_case_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False)
    person_ref:        Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)
    full_name:         Mapped[str]           = mapped_column(String(256), nullable=False)
    aliases:           Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    cpf:               Mapped[Optional[str]] = mapped_column(String(16),  nullable=True)
    rg:                Mapped[Optional[str]] = mapped_column(String(32),  nullable=True)
    birth_date:        Mapped[Optional[str]] = mapped_column(String(16),  nullable=True)
    notes:             Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    reliability_level: Mapped[Optional[str]] = mapped_column(String(32),  nullable=True)
    role_in_case:      Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)

    case: Mapped["SharedCase"] = relationship(back_populates="persons")


class SharedDocument(Base):
    __tablename__ = "shared_documents"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_case_id: Mapped[int]           = mapped_column(Integer, ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False)
    document_ref:   Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)
    filename:       Mapped[str]           = mapped_column(String(256), nullable=False)
    file_type:      Mapped[Optional[str]] = mapped_column(String(32),  nullable=True)
    sha256:         Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)
    description:    Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    imported_at:    Mapped[Optional[str]] = mapped_column(String(32),  nullable=True)

    case: Mapped["SharedCase"] = relationship(back_populates="documents")


class SharedLink(Base):
    __tablename__ = "shared_links"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_case_id: Mapped[int]           = mapped_column(Integer, ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False)
    link_type:      Mapped[str]           = mapped_column(String(32),  nullable=False)
    entity_a_ref:   Mapped[str]           = mapped_column(String(64),  nullable=False)
    entity_a_name:  Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    entity_b_ref:   Mapped[str]           = mapped_column(String(64),  nullable=False)
    entity_b_name:  Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    link_nature:    Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes:          Mapped[Optional[str]] = mapped_column(Text,        nullable=True)

    case: Mapped["SharedCase"] = relationship(back_populates="links")


class SharedCaseAnnotation(Base):
    """
    Anotação humana vinculada a um caso compartilhado.

    Não substitui SharedCase.notes, que pertence ao payload sincronizado.
    Registros desta tabela são criados por ação humana explícita e auditada.
    """
    __tablename__ = "shared_case_annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shared_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)

    case: Mapped["SharedCase"] = relationship(back_populates="annotations")

class PlateaAccessLog(Base):
    __tablename__ = "platea_access_log"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_case_id: Mapped[int]           = mapped_column(Integer, ForeignKey("shared_cases.id", ondelete="CASCADE"), nullable=False)
    case_ref:       Mapped[str]           = mapped_column(String(64),  nullable=False)
    operator_id:    Mapped[int]           = mapped_column(Integer,     nullable=False)
    operator_login: Mapped[str]           = mapped_column(String(128), nullable=False)
    accessed_at:    Mapped[datetime]      = mapped_column(DateTime,    nullable=False)
    ip_address:     Mapped[Optional[str]] = mapped_column(String(64),  nullable=True)

    case: Mapped["SharedCase"] = relationship(back_populates="accesses")