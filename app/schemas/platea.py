"""
Schemas Pydantic — Platea (AT-03)
Usados para validar o payload de sincronizacao vindo do Intel Desk
e para serializar respostas da API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ------------------------------------------------------------------
# Schemas de entrada (payload recebido do Intel Desk via POST /api/sync/case)
# ------------------------------------------------------------------

class PersonPayload(BaseModel):
    person_ref:        Optional[str] = None
    full_name:         str
    aliases:           Optional[str] = None
    cpf:               Optional[str] = None
    rg:                Optional[str] = None
    birth_date:        Optional[str] = None
    notes:             Optional[str] = None
    reliability_level: Optional[str] = None
    role_in_case:      Optional[str] = None


class DocumentPayload(BaseModel):
    document_ref: Optional[str] = None
    filename:     str
    file_type:    Optional[str] = None
    sha256:       Optional[str] = None
    description:  Optional[str] = None
    imported_at:  Optional[str] = None


class LinkPayload(BaseModel):
    link_type:     str
    entity_a_ref:  str
    entity_a_name: Optional[str] = None
    entity_b_ref:  str
    entity_b_name: Optional[str] = None
    link_nature:   Optional[str] = None
    notes:         Optional[str] = None


class SyncCasePayload(BaseModel):
    """Payload completo enviado pelo Intel Desk ao publicar um caso na Platea."""
    case_ref:       str
    title:          str
    status:         str
    classification: Optional[str] = None
    notes:          Optional[str] = None
    source_unit:    Optional[str] = None
    published_by:   str
    persons:        List[PersonPayload]   = []
    documents:      List[DocumentPayload] = []
    links:          List[LinkPayload]     = []


# ------------------------------------------------------------------
# Schemas de saída (respostas da API do Athena)
# ------------------------------------------------------------------

class PersonOut(BaseModel):
    id:                int
    person_ref:        Optional[str]
    full_name:         str
    aliases:           Optional[str]
    cpf:               Optional[str]
    rg:                Optional[str]
    birth_date:        Optional[str]
    notes:             Optional[str]
    reliability_level: Optional[str]
    role_in_case:      Optional[str]

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id:           int
    document_ref: Optional[str]
    filename:     str
    file_type:    Optional[str]
    sha256:       Optional[str]
    description:  Optional[str]
    imported_at:  Optional[str]

    model_config = {"from_attributes": True}


class LinkOut(BaseModel):
    id:            int
    link_type:     str
    entity_a_ref:  str
    entity_a_name: Optional[str]
    entity_b_ref:  str
    entity_b_name: Optional[str]
    link_nature:   Optional[str]
    notes:         Optional[str]

    model_config = {"from_attributes": True}


class SharedCaseListItem(BaseModel):
    """Item resumido para a listagem da Platea."""
    id:                int
    case_ref:          str
    title:             str
    status:            str
    classification:    Optional[str]
    source_unit:       Optional[str]
    published_by:      str
    published_at:      datetime
    published_version: int

    model_config = {"from_attributes": True}


class SharedCaseDetail(BaseModel):
    """Detalhe completo de um caso na Platea."""
    id:                int
    case_ref:          str
    title:             str
    status:            str
    classification:    Optional[str]
    notes:             Optional[str]
    source_unit:       Optional[str]
    published_by:      str
    published_at:      datetime
    published_version: int
    last_updated_at:   Optional[datetime]
    persons:           List[PersonOut]   = []
    documents:         List[DocumentOut] = []
    links:             List[LinkOut]     = []

    model_config = {"from_attributes": True}


class SyncResponse(BaseModel):
    """Resposta ao Intel Desk após receber um push."""
    case_ref:          str
    published_version: int
    status:            str   # "created" ou "updated"
    message:           str