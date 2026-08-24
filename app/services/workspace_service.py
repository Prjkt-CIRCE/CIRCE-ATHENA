from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models.platea import (
    SharedCase,
    SharedCaseAnnotation,
    SharedDocument,
    SharedLink,
    SharedPerson,
)
from app.models.workspace import (
    InvestigativeBlock,
    InvestigativeBlockSource,
    InvestigativeWorkspace,
)

MAX_BLOCK_SOURCES = 50
MAX_BLOCK_TITLE = 256
MAX_BLOCK_SUMMARY = 4000
VALID_SOURCE_TYPES = {"person", "document", "link", "annotation"}


@dataclass
class BlockContext:
    text: str
    sources: list[str]
    block_id: int
    case_ref: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fingerprint(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _normalize(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def get_workspace_for_case(db: Session, case_ref: str) -> InvestigativeWorkspace | None:
    case = db.query(SharedCase).filter(SharedCase.case_ref == case_ref).first()
    if not case:
        return None
    return (
        db.query(InvestigativeWorkspace)
        .filter(InvestigativeWorkspace.shared_case_id == case.id)
        .first()
    )


def open_workspace(
    db: Session,
    *,
    case_ref: str,
    operator_id: int | None,
    operator_username: str | None,
) -> tuple[InvestigativeWorkspace | None, bool]:
    case = db.query(SharedCase).filter(SharedCase.case_ref == case_ref).first()
    if not case:
        return None, False

    existing = (
        db.query(InvestigativeWorkspace)
        .filter(InvestigativeWorkspace.shared_case_id == case.id)
        .first()
    )
    if existing:
        return existing, False

    workspace = InvestigativeWorkspace(
        shared_case_id=case.id,
        created_by_operator_id=operator_id,
        created_by_username=operator_username or "operador",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(workspace)
    db.flush()
    return workspace, True


def list_blocks(db: Session, workspace_id: int) -> list[InvestigativeBlock]:
    return (
        db.query(InvestigativeBlock)
        .options(selectinload(InvestigativeBlock.sources))
        .filter(
            InvestigativeBlock.workspace_id == workspace_id,
            InvestigativeBlock.status != "discarded",
        )
        .order_by(InvestigativeBlock.updated_at.desc(), InvestigativeBlock.id.desc())
        .all()
    )


def resolve_case_source_token(db: Session, case: SharedCase, token: str) -> dict | None:
    if not isinstance(token, str) or ":" not in token:
        return None
    source_type, raw_id = token.split(":", 1)
    source_type = source_type.strip().lower()
    if source_type not in VALID_SOURCE_TYPES or not raw_id.isdigit():
        return None
    row_id = int(raw_id)

    if source_type == "person":
        obj = (
            db.query(SharedPerson)
            .filter(SharedPerson.id == row_id, SharedPerson.shared_case_id == case.id)
            .first()
        )
        if not obj:
            return None
        identity = {
            "full_name": obj.full_name,
            "person_ref": obj.person_ref,
            "cpf": obj.cpf,
            "rg": obj.rg,
            "birth_date": obj.birth_date,
        }
        if obj.person_ref:
            key = f"ref:{obj.person_ref}"
        elif obj.cpf:
            key = f"cpf:{obj.cpf}"
        elif obj.rg:
            key = f"rg:{obj.rg}"
        else:
            key = f"fingerprint:{_fingerprint(identity)}"
        return {
            "source_type": source_type,
            "source_key": key,
            "label": obj.full_name,
            "snapshot": identity | {
                "aliases": obj.aliases,
                "role_in_case": obj.role_in_case,
                "reliability_level": obj.reliability_level,
            },
        }

    if source_type == "document":
        obj = (
            db.query(SharedDocument)
            .filter(SharedDocument.id == row_id, SharedDocument.shared_case_id == case.id)
            .first()
        )
        if not obj:
            return None
        identity = {
            "document_ref": obj.document_ref,
            "filename": obj.filename,
            "file_type": obj.file_type,
            "sha256": obj.sha256,
            "imported_at": obj.imported_at,
        }
        if obj.document_ref:
            key = f"ref:{obj.document_ref}"
        elif obj.sha256:
            key = f"sha256:{obj.sha256}"
        else:
            key = f"fingerprint:{_fingerprint(identity)}"
        return {
            "source_type": source_type,
            "source_key": key,
            "label": obj.filename,
            "snapshot": identity | {"description": obj.description},
        }

    if source_type == "link":
        obj = (
            db.query(SharedLink)
            .filter(SharedLink.id == row_id, SharedLink.shared_case_id == case.id)
            .first()
        )
        if not obj:
            return None
        identity = {
            "link_type": obj.link_type,
            "entity_a_ref": obj.entity_a_ref,
            "entity_a_name": obj.entity_a_name,
            "entity_b_ref": obj.entity_b_ref,
            "entity_b_name": obj.entity_b_name,
            "link_nature": obj.link_nature,
        }
        label_a = obj.entity_a_name or obj.entity_a_ref
        label_b = obj.entity_b_name or obj.entity_b_ref
        return {
            "source_type": source_type,
            "source_key": f"fingerprint:{_fingerprint(identity)}",
            "label": f"{label_a} → {label_b}",
            "snapshot": identity | {"notes": obj.notes},
        }

    obj = (
        db.query(SharedCaseAnnotation)
        .filter(SharedCaseAnnotation.id == row_id, SharedCaseAnnotation.shared_case_id == case.id)
        .first()
    )
    if not obj:
        return None
    short = _normalize(obj.content)
    label = short[:96] + ("…" if len(short) > 96 else "")
    return {
        "source_type": source_type,
        "source_key": f"id:{obj.id}",
        "label": label or f"Anotação {obj.id}",
        "snapshot": {
            "annotation_id": obj.id,
            "content": obj.content,
            "created_by_username": obj.created_by_username,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "source": obj.source,
        },
    }


def create_block(
    db: Session,
    *,
    workspace_id: int,
    title: str,
    summary: str | None,
    source_tokens: list[str],
    operator_id: int | None,
    operator_username: str | None,
) -> tuple[InvestigativeBlock | None, str | None]:
    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if not workspace:
        return None, "Workspace não encontrado."

    case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
    if not case:
        return None, "Caso associado ao Workspace não foi encontrado."

    clean_title = _normalize(title)[:MAX_BLOCK_TITLE]
    clean_summary = (summary or "").strip()[:MAX_BLOCK_SUMMARY] or None
    if not clean_title:
        return None, "Informe um título para o bloco."

    unique_tokens = list(dict.fromkeys(source_tokens or []))[:MAX_BLOCK_SOURCES]
    if not unique_tokens:
        return None, "Selecione pelo menos um elemento do caso para criar o bloco."

    resolved: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for token in unique_tokens:
        item = resolve_case_source_token(db, case, token)
        if not item:
            return None, f"Fonte inválida ou fora do caso: {token}."
        identity = (item["source_type"], item["source_key"])
        if identity in seen:
            continue
        seen.add(identity)
        resolved.append(item)

    if not resolved:
        return None, "Nenhuma fonte válida foi selecionada."

    now = _utcnow()
    block = InvestigativeBlock(
        workspace_id=workspace.id,
        title=clean_title,
        summary=clean_summary,
        status="working",
        created_by_operator_id=operator_id,
        created_by_username=operator_username or "operador",
        authorship_mode="literal",
        created_at=now,
        updated_at=now,
    )
    db.add(block)
    db.flush()

    for position, item in enumerate(resolved):
        db.add(InvestigativeBlockSource(
            block_id=block.id,
            source_type=item["source_type"],
            source_key=item["source_key"],
            source_label_snapshot=item["label"],
            source_snapshot=json.dumps(item["snapshot"], ensure_ascii=False, sort_keys=True),
            relation="context",
            position=position,
            added_at=now,
        ))

    workspace.updated_at = now
    db.flush()
    return block, None


# AT06A_POOL_DND_V1
def add_block_sources(
    db: Session,
    *,
    workspace_id: int,
    block_id: int,
    source_tokens: list[str],
) -> tuple[InvestigativeBlock | None, list[InvestigativeBlockSource], str | None]:
    block = (
        db.query(InvestigativeBlock)
        .options(selectinload(InvestigativeBlock.sources))
        .filter(
            InvestigativeBlock.id == block_id,
            InvestigativeBlock.workspace_id == workspace_id,
            InvestigativeBlock.status != "discarded",
        )
        .first()
    )
    if not block:
        return None, [], "Bloco investigativo não encontrado."

    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if not workspace:
        return None, [], "Workspace não encontrado."

    case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
    if not case:
        return None, [], "Caso associado ao Workspace não foi encontrado."

    unique_tokens = list(dict.fromkeys(source_tokens or []))
    if not unique_tokens:
        return block, [], "Nenhuma fonte foi informada."

    existing = {(item.source_type, item.source_key) for item in block.sources}
    available_slots = MAX_BLOCK_SOURCES - len(existing)
    if available_slots <= 0:
        return block, [], f"O bloco já atingiu o limite de {MAX_BLOCK_SOURCES} fontes."

    resolved: list[dict] = []
    seen = set(existing)
    for token in unique_tokens:
        item = resolve_case_source_token(db, case, token)
        if not item:
            return block, [], f"Fonte inválida ou fora do caso: {token}."
        identity = (item["source_type"], item["source_key"])
        if identity in seen:
            continue
        seen.add(identity)
        resolved.append(item)
        if len(resolved) >= available_slots:
            break

    if not resolved:
        return block, [], None

    now = _utcnow()
    start_position = len(block.sources)
    added: list[InvestigativeBlockSource] = []

    for offset, item in enumerate(resolved):
        source = InvestigativeBlockSource(
            block_id=block.id,
            source_type=item["source_type"],
            source_key=item["source_key"],
            source_label_snapshot=item["label"],
            source_snapshot=json.dumps(item["snapshot"], ensure_ascii=False, sort_keys=True),
            relation="context",
            position=start_position + offset,
            added_at=now,
        )
        db.add(source)
        added.append(source)

    block.updated_at = now
    workspace.updated_at = now
    db.flush()
    block.sources.extend(item for item in added if item not in block.sources)
    return block, added, None


# AT06A_UNDO_V1
def remove_block_source(
    db: Session,
    *,
    workspace_id: int,
    block_id: int,
    source_id: int,
) -> tuple[InvestigativeBlockSource | None, str | None]:
    block = (
        db.query(InvestigativeBlock)
        .options(selectinload(InvestigativeBlock.sources))
        .filter(
            InvestigativeBlock.id == block_id,
            InvestigativeBlock.workspace_id == workspace_id,
            InvestigativeBlock.status != "discarded",
        )
        .first()
    )
    if not block:
        return None, "Bloco investigativo não encontrado."

    source = next((item for item in block.sources if item.id == source_id), None)
    if not source:
        return None, "Fonte não encontrada neste bloco."

    if len(block.sources) <= 1:
        return None, "O bloco deve manter pelo menos uma fonte. Desfaça o bloco inteiro se ele foi criado por engano."

    db.delete(source)

    remaining = [item for item in block.sources if item.id != source_id]
    for position, item in enumerate(remaining):
        item.position = position

    now = _utcnow()
    block.updated_at = now
    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if workspace:
        workspace.updated_at = now

    db.flush()
    return source, None


def discard_block(
    db: Session,
    *,
    workspace_id: int,
    block_id: int,
) -> tuple[InvestigativeBlock | None, str | None]:
    block = (
        db.query(InvestigativeBlock)
        .filter(
            InvestigativeBlock.id == block_id,
            InvestigativeBlock.workspace_id == workspace_id,
        )
        .first()
    )
    if not block:
        return None, "Bloco investigativo não encontrado."

    if block.status == "discarded":
        return block, None

    now = _utcnow()
    block.status = "discarded"
    block.updated_at = now

    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if workspace:
        workspace.updated_at = now

    db.flush()
    return block, None


def build_block_context(
    db: Session,
    *,
    case_ref: str | None,
    block_id: int | None,
) -> BlockContext | None:
    if not case_ref or not block_id:
        return None

    block = (
        db.query(InvestigativeBlock)
        .options(selectinload(InvestigativeBlock.sources))
        .filter(InvestigativeBlock.id == block_id)
        .first()
    )
    if not block or block.status == "discarded":
        return None

    workspace = db.query(InvestigativeWorkspace).filter_by(id=block.workspace_id).first()
    if not workspace:
        return None
    case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
    if not case or case.case_ref != case_ref:
        return None

    lines = [
        "CONTEXTO DO BLOCO INVESTIGATIVO ATIVO",
        f"[BLOCO:{block.id}]",
        f"caso: {case.case_ref}",
        f"titulo: {block.title}",
        f"status: {block.status}",
    ]
    if block.summary:
        lines.append(f"resumo_do_analista: {block.summary}")

    lines.append("fontes_do_bloco:")
    sources = [f"BLOCO:{block.id}"]
    for source in block.sources:
        marker = f"{source.source_type.upper()}:{source.source_key}"
        sources.append(marker)
        lines.append(
            f"- [{marker}] rotulo={source.source_label_snapshot}; "
            f"snapshot={source.source_snapshot or '{}'}"
        )

    lines.append(
        "Regra: o bloco organiza fontes e raciocínio. O texto do bloco não transforma "
        "inferência em fato e nenhuma fonte deve ser inventada."
    )
    return BlockContext(
        text="\n".join(lines),
        sources=sources,
        block_id=block.id,
        case_ref=case.case_ref,
    )
