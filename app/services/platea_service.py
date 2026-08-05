"""
platea_service.py — AT-03.3
Logica de recepcao, persistencia e audit log da Platea.

Contrato:
- receive_case_sync: cria ou atualiza caso compartilhado atomicamente.
  Se case_ref ja existe: apaga filhos (cascade) e reinserere com versao incrementada.
- log_platea_access: registra acesso ao detalhe de caso (append-only).
- get_case_list: retorna lista paginada de casos para /platea.
- get_case_detail: retorna caso completo por case_ref.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.platea import (
    SharedCase, SharedPerson, SharedDocument, SharedLink, PlateaAccessLog
)
from app.models.operator import AuditLog
from app.schemas.platea import SyncCasePayload, SyncResponse


# ------------------------------------------------------------------
# Helpers internos
# ------------------------------------------------------------------

def _last_audit_hash(db: Session) -> str:
    """Retorna o hash do ultimo registro de auditoria, ou hash genesis."""
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    return last.current_hash if last else "0" * 64


def _write_audit(
    db: Session,
    operator_id: Optional[int],
    operator_username: Optional[str],
    action: str,
    entity_type: str,
    entity_id: str,
    description: str,
    ip_address: Optional[str] = None,
) -> None:
    """Escreve entrada no audit log seguindo o contrato ADR-003/003a."""
    now = datetime.now(timezone.utc)
    previous_hash = _last_audit_hash(db)
    current_hash = AuditLog.compute_hash(
        previous_hash=previous_hash,
        timestamp=now.isoformat(),
        operator_username=operator_username or "",
        action=action,
        description=description,
    )
    entry = AuditLog(
        timestamp=now,
        operator_id=operator_id,
        operator_username=operator_username,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.add(entry)


# ------------------------------------------------------------------
# receive_case_sync
# ------------------------------------------------------------------

def receive_case_sync(
    db: Session,
    payload: SyncCasePayload,
    operator_id: int,
    operator_username: str,
    ip_address: Optional[str] = None,
) -> SyncResponse:
    """
    Recebe payload do Intel Desk e persiste na Platea.
    - Se case_ref nao existe: cria com versao 1.
    - Se case_ref ja existe: apaga filhos via cascade e reinserere
      com versao incrementada. Ultima versao vence (D-AT-018).
    Tudo numa unica transacao: falha = rollback total.
    """
    now = datetime.now(timezone.utc)

    existing = db.query(SharedCase).filter_by(case_ref=payload.case_ref).first()

    if existing:
        # Atualiza campos do caso
        new_version = existing.published_version + 1
        existing.title             = payload.title
        existing.status            = payload.status
        existing.classification    = payload.classification
        existing.notes             = payload.notes
        existing.source_unit       = payload.source_unit
        existing.published_by      = payload.published_by
        existing.published_version = new_version
        existing.last_updated_at   = now

        # Remove filhos antigos (cascade cuida do DELETE, mas forcamos flush
        # para garantir ordem antes de reinserir)
        for child_list in (existing.persons, existing.documents, existing.links):
            for child in list(child_list):
                db.delete(child)
        db.flush()

        shared_case = existing
        event_status = "updated"
        action = "PLATEA_CASE_UPDATED"
        description = (
            f"Caso {payload.case_ref} atualizado na Platea por {payload.published_by} "
            f"(versao {new_version}, unidade: {payload.source_unit or 'nao informada'})"
        )
    else:
        shared_case = SharedCase(
            case_ref          = payload.case_ref,
            title             = payload.title,
            status            = payload.status,
            classification    = payload.classification,
            notes             = payload.notes,
            source_unit       = payload.source_unit,
            published_by      = payload.published_by,
            published_at      = now,
            published_version = 1,
        )
        db.add(shared_case)
        db.flush()  # gera shared_case.id antes de inserir filhos

        new_version  = 1
        event_status = "created"
        action       = "PLATEA_CASE_PUBLISHED"
        description  = (
            f"Caso {payload.case_ref} publicado na Platea por {payload.published_by} "
            f"(unidade: {payload.source_unit or 'nao informada'})"
        )

    # Insere filhos
    for p in payload.persons:
        db.add(SharedPerson(
            shared_case_id    = shared_case.id,
            person_ref        = p.person_ref,
            full_name         = p.full_name,
            aliases           = p.aliases,
            cpf               = p.cpf,
            rg                = p.rg,
            birth_date        = p.birth_date,
            notes             = p.notes,
            reliability_level = p.reliability_level,
            role_in_case      = p.role_in_case,
        ))

    for d in payload.documents:
        db.add(SharedDocument(
            shared_case_id = shared_case.id,
            document_ref   = d.document_ref,
            filename       = d.filename,
            file_type      = d.file_type,
            sha256         = d.sha256,
            description    = d.description,
            imported_at    = d.imported_at,
        ))

    for lk in payload.links:
        db.add(SharedLink(
            shared_case_id = shared_case.id,
            link_type      = lk.link_type,
            entity_a_ref   = lk.entity_a_ref,
            entity_a_name  = lk.entity_a_name,
            entity_b_ref   = lk.entity_b_ref,
            entity_b_name  = lk.entity_b_name,
            link_nature    = lk.link_nature,
            notes          = lk.notes,
        ))

    # Audit log (dentro da mesma transacao)
    _write_audit(
        db=db,
        operator_id=operator_id,
        operator_username=operator_username,
        action=action,
        entity_type="shared_case",
        entity_id=payload.case_ref,
        description=description,
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(shared_case)

    return SyncResponse(
        case_ref          = payload.case_ref,
        published_version = new_version,
        status            = event_status,
        message           = description,
    )


# ------------------------------------------------------------------
# log_platea_access
# ------------------------------------------------------------------

def log_platea_access(
    db: Session,
    shared_case: SharedCase,
    operator_id: int,
    operator_login: str,
    ip_address: Optional[str] = None,
) -> None:
    """
    Registra acesso ao detalhe de caso na Platea.
    Append-only — nunca editado ou excluido pela interface (A4/adendo modelo ameacas).
    Tambem escreve no audit log central.
    """
    now = datetime.now(timezone.utc)

    access = PlateaAccessLog(
        shared_case_id = shared_case.id,
        case_ref       = shared_case.case_ref,
        operator_id    = operator_id,
        operator_login = operator_login,
        accessed_at    = now,
        ip_address     = ip_address,
    )
    db.add(access)

    _write_audit(
        db=db,
        operator_id=operator_id,
        operator_username=operator_login,
        action="PLATEA_CASE_ACCESSED",
        entity_type="shared_case",
        entity_id=shared_case.case_ref,
        description=(
            f"Caso {shared_case.case_ref} acessado na Platea por {operator_login}"
        ),
        ip_address=ip_address,
    )

    db.commit()


# ------------------------------------------------------------------
# Consultas
# ------------------------------------------------------------------

def get_case_list(db: Session, skip: int = 0, limit: int = 50):
    """Lista paginada de casos compartilhados, mais recentes primeiro."""
    return (
        db.query(SharedCase)
        .order_by(SharedCase.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_case_by_ref(db: Session, case_ref: str) -> Optional[SharedCase]:
    """Retorna caso completo por case_ref, ou None se nao encontrado."""
    return db.query(SharedCase).filter_by(case_ref=case_ref).first()


def count_cases(db: Session) -> int:
    """Total de casos na Platea (para paginacao)."""
    return db.query(SharedCase).count()