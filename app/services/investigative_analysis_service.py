from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.platea import SharedCase
from app.models.workspace import (
    InvestigativeExcerpt,
    InvestigativeExcerptSource,
    InvestigativeFinding,
    InvestigativeWorkspace,
    InvestigativeWorkTopic,
)
from app.services.workspace_service import resolve_case_source_token

MAX_EXCERPT_SOURCES = 30
MAX_ANALYST_NOTE = 8000
MAX_TITLE = 256
MAX_SUMMARY = 6000
MAX_INTERPRETATION = 6000
VALID_FINDING_TYPES = {
    "fact",
    "declaration",
    "annotation",
    "inference",
    "hypothesis",
    "pending",
}


@dataclass
class AnalysisProposal:
    title: str
    objective_summary: str
    interpretation: str
    suggested_type: str
    support_gaps: list[str]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value: object, limit: int) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def resolve_excerpt_sources(
    db: Session,
    *,
    workspace_id: int,
    source_tokens: list[str],
) -> tuple[InvestigativeWorkspace | None, SharedCase | None, list[dict], str | None]:
    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if not workspace:
        return None, None, [], "Workspace não encontrado."

    case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
    if not case:
        return workspace, None, [], "Caso associado ao Workspace não foi encontrado."

    unique_tokens = list(dict.fromkeys(source_tokens or []))[:MAX_EXCERPT_SOURCES]
    if not unique_tokens:
        return workspace, case, [], "Selecione pelo menos um elemento do Pool."

    resolved: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for token in unique_tokens:
        item = resolve_case_source_token(db, case, token)
        if not item:
            return workspace, case, [], f"Fonte inválida ou fora do caso: {token}."
        identity = (item["source_type"], item["source_key"])
        if identity in seen:
            continue
        seen.add(identity)
        resolved.append(item)

    if not resolved:
        return workspace, case, [], "Nenhuma fonte válida foi selecionada."

    return workspace, case, resolved, None


def _proposal_prompt(
    *,
    case_ref: str,
    analyst_note: str,
    sources: list[dict],
    work_topic: InvestigativeWorkTopic | None = None,
) -> str:
    source_payload = []
    for index, source in enumerate(sources, start=1):
        snapshot = json.dumps(source.get("snapshot") or {}, ensure_ascii=False, sort_keys=True, default=str)
        source_payload.append({
            "index": index,
            "type": source.get("source_type"),
            "label": source.get("label"),
            "snapshot": snapshot[:3000],
        })

    return (
        "Você está estruturando um RECORTE INVESTIGATIVO para um policial. "
        "A nota do analista é uma observação humana e NÃO deve ser convertida automaticamente em fato. "
        "Use somente a nota e as fontes fornecidas. Não invente conteúdo ausente. "
        "Separe descrição objetiva de interpretação. Preserve expressões de incerteza como 'em tese', "
        "'aparenta', 'pode indicar' e equivalentes quando a sustentação não for conclusiva. "
        "Se as fontes disponibilizadas contiverem apenas metadados insuficientes para sustentar a nota, "
        "registre essa limitação em support_gaps. "
        "Retorne EXCLUSIVAMENTE um objeto JSON válido, sem markdown, com as chaves: "
        "title, objective_summary, interpretation, suggested_type, support_gaps. "
        "suggested_type deve ser um de: fact, declaration, annotation, inference, hypothesis, pending. "
        "objective_summary deve descrever o que está diretamente registrado nas fontes/nota, sem elevar inferência a fato. "
        "interpretation deve registrar a leitura analítica proposta, quando houver, explicitando que depende de validação humana.\n\n"
        f"CASO: {case_ref}\n"
        f"TOPICO_DE_TRABALHO: {work_topic.title if work_topic else 'não informado'}\n"
        f"OBJETIVO_DO_TOPICO: {(work_topic.purpose or '') if work_topic else ''}\n"
        f"NOTA_LITERAL_DO_ANALISTA: {analyst_note}\n"
        f"FONTES_SELECIONADAS: {json.dumps(source_payload, ensure_ascii=False)}"
    )


def _extract_json_object(raw: str) -> dict:
    text = (raw or "").strip()
    if not text:
        raise ValueError("Athena retornou conteúdo vazio.")
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Athena não retornou JSON estruturado.")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Resposta estruturada inválida.")
    return value


async def propose_analysis(
    *,
    case_ref: str,
    analyst_note: str,
    sources: list[dict],
    work_topic: InvestigativeWorkTopic | None = None,
) -> AnalysisProposal:
    note = analyst_note.strip()[:MAX_ANALYST_NOTE]
    if not note:
        raise ValueError("Registre a percepção do analista antes de estruturar o recorte.")

    prompt = _proposal_prompt(
        case_ref=case_ref,
        analyst_note=note,
        sources=sources,
        work_topic=work_topic,
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.llm_base_url}/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é Athena, assistente de inteligência local. "
                            "Sua função aqui é estruturar a nota do policial sem assumir autoria da decisão investigativa."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            headers={"Authorization": "Bearer lm-studio"},
        )
        response.raise_for_status()

    data = response.json()
    raw = data["choices"][0]["message"].get("content") or ""
    parsed = _extract_json_object(raw)

    support_gaps = parsed.get("support_gaps")
    if not isinstance(support_gaps, list):
        support_gaps = []
    clean_gaps = [_clean(item, 600) for item in support_gaps if _clean(item, 600)][:12]

    suggested = _clean(parsed.get("suggested_type"), 32).lower()
    if suggested not in VALID_FINDING_TYPES:
        suggested = "annotation"

    title = _clean(parsed.get("title"), MAX_TITLE) or "Recorte investigativo"
    summary = str(parsed.get("objective_summary") or "").strip()[:MAX_SUMMARY]
    interpretation = str(parsed.get("interpretation") or "").strip()[:MAX_INTERPRETATION]
    if not summary:
        raise ValueError("Athena não produziu resumo objetivo utilizável.")

    return AnalysisProposal(
        title=title,
        objective_summary=summary,
        interpretation=interpretation,
        suggested_type=suggested,
        support_gaps=clean_gaps,
    )


def create_excerpt_draft(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    analyst_note: str,
    sources: list[dict],
    proposal: AnalysisProposal,
    operator_id: int | None,
    operator_username: str | None,
    work_topic_id: int | None = None,
) -> InvestigativeExcerpt:
    now = _utcnow()
    excerpt = InvestigativeExcerpt(
        workspace_id=workspace.id,
        work_topic_id=work_topic_id,
        title=proposal.title,
        analyst_note=analyst_note.strip()[:MAX_ANALYST_NOTE],
        proposed_summary=proposal.objective_summary,
        proposed_interpretation=proposal.interpretation or None,
        suggested_type=proposal.suggested_type,
        support_gaps=json.dumps(proposal.support_gaps, ensure_ascii=False),
        status="draft",
        created_by_operator_id=operator_id,
        created_by_username=operator_username or "operador",
        created_at=now,
        updated_at=now,
    )
    db.add(excerpt)
    db.flush()

    for position, source in enumerate(sources):
        db.add(InvestigativeExcerptSource(
            excerpt_id=excerpt.id,
            source_type=source["source_type"],
            source_key=source["source_key"],
            source_label_snapshot=source["label"],
            source_snapshot=json.dumps(source.get("snapshot") or {}, ensure_ascii=False, sort_keys=True, default=str),
            position=position,
            added_at=now,
        ))

    workspace.updated_at = now
    db.flush()
    return excerpt


def list_excerpt_drafts(db: Session, workspace_id: int) -> list[InvestigativeExcerpt]:
    return (
        db.query(InvestigativeExcerpt)
        .options(selectinload(InvestigativeExcerpt.sources))
        .filter(
            InvestigativeExcerpt.workspace_id == workspace_id,
            InvestigativeExcerpt.status == "draft",
        )
        .order_by(InvestigativeExcerpt.updated_at.desc(), InvestigativeExcerpt.id.desc())
        .all()
    )


def list_findings(db: Session, workspace_id: int) -> list[InvestigativeFinding]:
    return (
        db.query(InvestigativeFinding)
        .options(
            selectinload(InvestigativeFinding.excerpt).selectinload(InvestigativeExcerpt.sources)
        )
        .filter(
            InvestigativeFinding.workspace_id == workspace_id,
            InvestigativeFinding.status == "validated",
        )
        .order_by(InvestigativeFinding.validated_at.desc(), InvestigativeFinding.id.desc())
        .all()
    )


def validate_finding(
    db: Session,
    *,
    workspace_id: int,
    excerpt_id: int,
    title: str,
    objective_summary: str,
    interpretation: str | None,
    finding_type: str,
    operator_id: int | None,
    operator_username: str | None,
) -> tuple[InvestigativeFinding | None, str | None]:
    excerpt = (
        db.query(InvestigativeExcerpt)
        .options(selectinload(InvestigativeExcerpt.sources))
        .filter(
            InvestigativeExcerpt.id == excerpt_id,
            InvestigativeExcerpt.workspace_id == workspace_id,
        )
        .first()
    )
    if not excerpt:
        return None, "Recorte investigativo não encontrado."
    if excerpt.status != "draft":
        return None, "Este recorte não está mais em estado de validação."
    if excerpt.finding is not None:
        return None, "Este recorte já originou um Achado."

    clean_title = _clean(title, MAX_TITLE)
    clean_summary = str(objective_summary or "").strip()[:MAX_SUMMARY]
    clean_interpretation = str(interpretation or "").strip()[:MAX_INTERPRETATION] or None
    clean_type = _clean(finding_type, 32).lower()

    if not clean_title:
        return None, "Informe um título para o Achado."
    if not clean_summary:
        return None, "O Achado precisa de um resumo objetivo."
    if clean_type not in VALID_FINDING_TYPES:
        return None, "Classificação epistemológica inválida."

    now = _utcnow()
    finding = InvestigativeFinding(
        workspace_id=workspace_id,
        work_topic_id=excerpt.work_topic_id,
        excerpt_id=excerpt.id,
        title=clean_title,
        objective_summary=clean_summary,
        interpretation=clean_interpretation,
        finding_type=clean_type,
        status="validated",
        authorship_mode="assisted_drafting",
        validated_by_operator_id=operator_id,
        validated_by_username=operator_username or "operador",
        validated_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    excerpt.status = "promoted"
    excerpt.updated_at = now
    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if workspace:
        workspace.updated_at = now
    db.flush()
    return finding, None


def discard_excerpt(
    db: Session,
    *,
    workspace_id: int,
    excerpt_id: int,
) -> tuple[InvestigativeExcerpt | None, str | None]:
    excerpt = (
        db.query(InvestigativeExcerpt)
        .filter(
            InvestigativeExcerpt.id == excerpt_id,
            InvestigativeExcerpt.workspace_id == workspace_id,
        )
        .first()
    )
    if not excerpt:
        return None, "Recorte investigativo não encontrado."
    if excerpt.status != "draft":
        return None, "Somente recortes em rascunho podem ser descartados."

    now = _utcnow()
    excerpt.status = "discarded"
    excerpt.updated_at = now
    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if workspace:
        workspace.updated_at = now
    db.flush()
    return excerpt, None
