from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.platea import SharedDocument
from app.models.reporting import (
    WorkspaceTopicComposition,
    WorkspaceTopicCompositionSource,
    WorkspaceTopicFact,
    WorkspaceTopicNarrativeBlock,
    WorkspaceTopicNarrativeBlockSource,
)
from app.models.workspace import InvestigativeWorkTopic, InvestigativeWorkspace
from app.services.report_header_extraction_service import PdfPageText, extract_pdf_pages

FACT_SCHEMA = (
    ("investigation_origin", "Origem da apuração"),
    ("event_nature", "Natureza do fato"),
    ("event_date", "Data / período do fato"),
    ("event_location", "Local"),
    ("victims", "Vítima(s) / alvo(s)"),
    ("persons_mentioned", "Pessoas mencionadas"),
    ("event_summary", "Síntese objetiva do fato"),
    ("report_scope", "Delimitação desta análise"),
)
VALID_FACT_STATUS = {"proposed", "confirmed", "ignored"}
MAX_TOTAL_CHARS = 80000
MAX_CONTEXT_CHARS = 12000
MAX_BLOCK_CHARS = 12000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _extract_json_object(raw: str) -> dict:
    text = str(raw or "").strip()
    if not text:
        raise ValueError("Athena retornou resposta vazia.")
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


def get_topic_composition(
    db: Session,
    *,
    workspace_id: int,
    work_topic_id: int,
) -> WorkspaceTopicComposition | None:
    return (
        db.query(WorkspaceTopicComposition)
        .options(
            selectinload(WorkspaceTopicComposition.sources),
            selectinload(WorkspaceTopicComposition.facts),
            selectinload(WorkspaceTopicComposition.narrative_blocks).selectinload(
                WorkspaceTopicNarrativeBlock.sources
            ),
        )
        .filter(
            WorkspaceTopicComposition.workspace_id == workspace_id,
            WorkspaceTopicComposition.work_topic_id == work_topic_id,
        )
        .first()
    )


def get_or_create_topic_composition(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    work_topic: InvestigativeWorkTopic,
    operator_username: str | None,
) -> WorkspaceTopicComposition:
    item = get_topic_composition(
        db,
        workspace_id=workspace.id,
        work_topic_id=work_topic.id,
    )
    if item:
        return item
    now = _utcnow()
    item = WorkspaceTopicComposition(
        workspace_id=workspace.id,
        work_topic_id=work_topic.id,
        analyst_context=None,
        status="draft",
        updated_by_username=operator_username or "operador",
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    db.flush()
    return item


def composition_payload(item: WorkspaceTopicComposition | None) -> dict:
    if not item:
        return {
            "id": None,
            "status": "draft",
            "analyst_context": "",
            "sources": [],
            "facts": [],
            "narrative_blocks": [],
        }
    return {
        "id": item.id,
        "status": item.status,
        "analyst_context": item.analyst_context or "",
        "sources": [
            {
                "source_type": source.source_type,
                "source_key": source.source_key,
                "label": source.source_label_snapshot,
            }
            for source in item.sources
        ],
        "facts": [
            {
                "id": fact.id,
                "fact_key": fact.fact_key,
                "label": fact.label,
                "value": fact.value or "",
                "status": fact.status,
                "source_document_id": fact.source_document_id,
                "source_label": fact.source_label_snapshot or "",
                "page": fact.page_number,
                "excerpt": fact.excerpt or "",
                "confidence": fact.confidence,
                "notes": fact.notes or "",
                "position": fact.position,
            }
            for fact in item.facts
        ],
        "narrative_blocks": [
            {
                "id": block.id,
                "block_key": block.block_key,
                "title": block.title,
                "body": block.body or "",
                "position": block.position,
                "sources": [
                    {
                        "source_document_id": source.source_document_id,
                        "source_label": source.source_label_snapshot or "",
                        "page": source.page_number,
                        "excerpt": source.excerpt or "",
                    }
                    for source in block.sources
                ],
            }
            for block in item.narrative_blocks
        ],
    }


def source_tokens(item: WorkspaceTopicComposition | None) -> list[str]:
    if not item:
        return []
    tokens: list[str] = []
    for source in item.sources:
        key = str(source.source_key or "")
        if source.source_type == "document" and key.startswith("DOCID:"):
            tokens.append(f"document:{key.split(':', 1)[1]}")
    return tokens


def _page_material(pages: list[PdfPageText]) -> str:
    blocks: list[str] = []
    used = 0
    for page in pages:
        block = (
            f"\n--- DOCUMENTO_ID={page.document_id} | ARQUIVO={page.filename} | PAGINA={page.page_number} ---\n"
            f"{page.text}\n"
        )
        if used + len(block) > MAX_TOTAL_CHARS:
            break
        blocks.append(block)
        used += len(block)
    return "".join(blocks)


def _fact_prompt(pages: list[PdfPageText], topic: InvestigativeWorkTopic) -> str:
    schema = {
        key: {
            "value": "",
            "source_document_id": None,
            "page": None,
            "excerpt": "",
            "confidence": 0.0,
            "notes": "",
        }
        for key, _ in FACT_SCHEMA
    }
    return (
        "Você está preparando o MAPA FACTUAL do tópico 'Dos fatos / introdução' de um relatório policial. "
        "Extraia SOMENTE informações explicitamente sustentadas pelos documentos fornecidos. Não invente, não complete lacunas e não transforme hipótese em fato. "
        "Se houver divergência relevante entre fontes, escolha o valor mais diretamente sustentado apenas quando isso for inequívoco; caso contrário deixe value vazio e descreva a divergência em notes. "
        "Campos: investigation_origin=origem da apuração/atuação da unidade; event_nature=natureza do fato investigado; "
        "event_date=data ou período do fato; event_location=local; victims=vítimas/alvos; persons_mentioned=pessoas nominalmente mencionadas; "
        "event_summary=síntese objetiva do fato; report_scope=objetivo/delimitação da análise quando expressamente informado. "
        "source_document_id DEVE corresponder a um DOCUMENTO_ID fornecido. page é a página que sustenta o valor. excerpt é trecho curto e fiel da fonte. confidence entre 0 e 1. "
        "Retorne SOMENTE JSON válido, sem markdown, exatamente no formato "
        f"{{\"facts\": {json.dumps(schema, ensure_ascii=False)}, \"notes\": []}}.\n"
        f"TÓPICO: {topic.title}\nOBJETIVO: {topic.purpose or ''}\nMATERIAL:" + _page_material(pages)
    )


async def propose_fact_map(
    *,
    documents: list[SharedDocument],
    topic: InvestigativeWorkTopic,
) -> tuple[list[dict], list[str], list[str]]:
    pages: list[PdfPageText] = []
    warnings: list[str] = []
    for document in documents:
        extracted, item_warnings = extract_pdf_pages(document)
        pages.extend(extracted)
        warnings.extend(item_warnings)
    if not pages:
        raise ValueError(
            "Nenhum texto de PDF pôde ser extraído. Se os documentos forem imagens digitalizadas, será necessário OCR."
        )

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{settings.llm_base_url}/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é Athena, assistente local de inteligência policial. "
                            "Nesta etapa você extrai um mapa factual com proveniência e não redige conclusões."
                        ),
                    },
                    {"role": "user", "content": _fact_prompt(pages, topic)},
                ],
                "temperature": 0,
                "max_tokens": 3200,
            },
            headers={"Authorization": "Bearer lm-studio"},
        )
        response.raise_for_status()

    data = response.json()
    raw = data["choices"][0]["message"].get("content") or ""
    parsed = _extract_json_object(raw)
    raw_facts = parsed.get("facts") if isinstance(parsed.get("facts"), dict) else {}
    valid_documents = {item.id: item for item in documents}
    facts: list[dict] = []
    for position, (key, label) in enumerate(FACT_SCHEMA):
        item = raw_facts.get(key) if isinstance(raw_facts.get(key), dict) else {}
        value = str(item.get("value") or "").strip()[:5000]
        source_id = item.get("source_document_id")
        try:
            source_id = int(source_id) if source_id not in (None, "") else None
        except (TypeError, ValueError):
            source_id = None
        if source_id not in valid_documents:
            source_id = None
        page = item.get("page")
        try:
            page = int(page) if page not in (None, "") else None
        except (TypeError, ValueError):
            page = None
        confidence = item.get("confidence")
        try:
            confidence = float(confidence) if confidence not in (None, "") else None
        except (TypeError, ValueError):
            confidence = None
        if confidence is not None:
            confidence = max(0.0, min(1.0, confidence))
        document = valid_documents.get(source_id) if source_id else None
        facts.append({
            "fact_key": key,
            "label": label,
            "value": value,
            "source_document_id": source_id,
            "source_label": document.filename if document else None,
            "page": page,
            "excerpt": str(item.get("excerpt") or "").strip()[:1500],
            "confidence": confidence,
            "notes": str(item.get("notes") or "").strip()[:1500],
            "position": position,
        })
    notes = parsed.get("notes") if isinstance(parsed.get("notes"), list) else []
    clean_notes = [str(item).strip()[:600] for item in notes if str(item).strip()][:12]
    return facts, warnings, clean_notes


def store_fact_map(
    db: Session,
    *,
    composition: WorkspaceTopicComposition,
    resolved_sources: list[dict],
    facts: list[dict],
    operator_username: str | None,
) -> None:
    now = _utcnow()
    composition.sources.clear()
    composition.facts.clear()
    composition.narrative_blocks.clear()
    db.flush()

    for source in resolved_sources:
        composition.sources.append(
            WorkspaceTopicCompositionSource(
                source_type=source["source_type"],
                source_key=source["source_key"],
                source_label_snapshot=source["label"],
                created_at=now,
            )
        )
    for item in facts:
        composition.facts.append(
            WorkspaceTopicFact(
                fact_key=item["fact_key"],
                label=item["label"],
                value=item.get("value") or None,
                status="proposed",
                source_document_id=item.get("source_document_id"),
                source_label_snapshot=item.get("source_label"),
                page_number=item.get("page"),
                excerpt=item.get("excerpt") or None,
                confidence=item.get("confidence"),
                notes=item.get("notes") or None,
                position=int(item.get("position") or 0),
                created_at=now,
                updated_at=now,
            )
        )
    composition.status = "draft"
    composition.confirmed_by_username = None
    composition.confirmed_at = None
    composition.updated_by_username = operator_username or "operador"
    composition.updated_at = now
    db.flush()


def save_fact_map(
    db: Session,
    *,
    composition: WorkspaceTopicComposition,
    analyst_context: str | None,
    facts: list[dict],
    operator_username: str | None,
) -> None:
    by_id = {item.id: item for item in composition.facts}
    by_key = {item.fact_key: item for item in composition.facts}
    now = _utcnow()
    for payload in facts:
        target = None
        try:
            fact_id = int(payload.get("id")) if payload.get("id") not in (None, "") else None
        except (TypeError, ValueError):
            fact_id = None
        if fact_id:
            target = by_id.get(fact_id)
        if not target:
            target = by_key.get(str(payload.get("fact_key") or ""))
        if not target:
            continue
        target.value = str(payload.get("value") or "").strip()[:5000] or None
        status = str(payload.get("status") or "proposed").strip().lower()
        target.status = status if status in VALID_FACT_STATUS else "proposed"
        target.updated_at = now

    composition.analyst_context = str(analyst_context or "").strip()[:MAX_CONTEXT_CHARS] or None
    composition.status = "draft"
    composition.confirmed_by_username = None
    composition.confirmed_at = None
    composition.updated_by_username = operator_username or "operador"
    composition.updated_at = now
    db.flush()


def _narrative_prompt(composition: WorkspaceTopicComposition, topic: InvestigativeWorkTopic) -> str:
    confirmed = [fact for fact in composition.facts if fact.status == "confirmed" and (fact.value or "").strip()]
    if not confirmed and not (composition.analyst_context or "").strip():
        raise ValueError("Confirme ao menos um item do mapa factual ou registre contexto do analista antes de compor a narrativa.")

    facts = [
        {
            "fact_key": fact.fact_key,
            "label": fact.label,
            "value": fact.value,
            "source_document_id": fact.source_document_id,
            "source_label": fact.source_label_snapshot,
            "page": fact.page_number,
            "excerpt": fact.excerpt,
        }
        for fact in confirmed
    ]
    return (
        "Você está compondo o tópico 'Dos fatos / introdução' de um relatório policial. "
        "Use SOMENTE os fatos confirmados e o contexto literal do analista fornecidos. Não acrescente dados, nomes, datas ou conclusões ausentes. "
        "Redija em estilo técnico, objetivo, sóbrio e cronológico quando houver cronologia. Preserve incerteza quando o contexto humano indicar dúvida. "
        "Divida em no máximo três blocos curtos: origin_context=origem/contextualização; event_summary=síntese dos fatos; analysis_scope=delimitação/objetivo da análise. "
        "Cada bloco deve informar fact_keys utilizados. Se um bloco não tiver conteúdo suficiente, devolva body vazio. "
        "Retorne SOMENTE JSON válido: {\"blocks\":[{\"block_key\":\"origin_context\",\"title\":\"Origem da apuração\",\"body\":\"\",\"fact_keys\":[]},"
        "{\"block_key\":\"event_summary\",\"title\":\"Síntese dos fatos\",\"body\":\"\",\"fact_keys\":[]},"
        "{\"block_key\":\"analysis_scope\",\"title\":\"Delimitação da análise\",\"body\":\"\",\"fact_keys\":[]}]}\n"
        f"TÓPICO: {topic.title}\nOBJETIVO: {topic.purpose or ''}\n"
        f"FATOS_CONFIRMADOS: {json.dumps(facts, ensure_ascii=False)}\n"
        f"CONTEXTO_LITERAL_DO_ANALISTA: {(composition.analyst_context or '').strip()}"
    )


async def propose_narrative_blocks(
    *,
    composition: WorkspaceTopicComposition,
    topic: InvestigativeWorkTopic,
) -> list[dict]:
    prompt = _narrative_prompt(composition, topic)
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{settings.llm_base_url}/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é Athena, assistente local de inteligência policial. "
                            "Você redige somente a partir de fatos confirmados pelo policial e contexto humano autorizado."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.15,
                "max_tokens": 2600,
            },
            headers={"Authorization": "Bearer lm-studio"},
        )
        response.raise_for_status()

    data = response.json()
    raw = data["choices"][0]["message"].get("content") or ""
    parsed = _extract_json_object(raw)
    items = parsed.get("blocks") if isinstance(parsed.get("blocks"), list) else []
    result: list[dict] = []
    allowed_keys = {fact.fact_key for fact in composition.facts if fact.status == "confirmed"}
    for position, item in enumerate(items[:3]):
        if not isinstance(item, dict):
            continue
        block_key = str(item.get("block_key") or f"block_{position+1}").strip()[:96]
        title = str(item.get("title") or f"Bloco {position+1}").strip()[:256]
        body = str(item.get("body") or "").strip()[:MAX_BLOCK_CHARS]
        raw_keys = item.get("fact_keys") if isinstance(item.get("fact_keys"), list) else []
        fact_keys = [str(key) for key in raw_keys if str(key) in allowed_keys]
        result.append({
            "block_key": block_key,
            "title": title,
            "body": body,
            "position": position,
            "fact_keys": fact_keys,
        })
    return result


def store_narrative_blocks(
    db: Session,
    *,
    composition: WorkspaceTopicComposition,
    blocks: list[dict],
    operator_username: str | None,
) -> None:
    fact_by_key = {fact.fact_key: fact for fact in composition.facts}
    composition.narrative_blocks.clear()
    db.flush()
    now = _utcnow()
    for item in blocks:
        block = WorkspaceTopicNarrativeBlock(
            block_key=str(item.get("block_key") or "").strip()[:96],
            title=str(item.get("title") or "").strip()[:256] or "Bloco narrativo",
            body=str(item.get("body") or "").strip()[:MAX_BLOCK_CHARS] or None,
            position=int(item.get("position") or 0),
            authorship_mode="assisted_drafting",
            created_at=now,
            updated_at=now,
        )
        composition.narrative_blocks.append(block)
        db.flush()
        seen: set[tuple[int | None, int | None, str]] = set()
        for fact_key in item.get("fact_keys") or []:
            fact = fact_by_key.get(str(fact_key))
            if not fact:
                continue
            identity = (fact.source_document_id, fact.page_number, fact.excerpt or "")
            if identity in seen:
                continue
            seen.add(identity)
            block.sources.append(
                WorkspaceTopicNarrativeBlockSource(
                    source_document_id=fact.source_document_id,
                    source_label_snapshot=fact.source_label_snapshot,
                    page_number=fact.page_number,
                    excerpt=fact.excerpt,
                    created_at=now,
                )
            )
    composition.status = "draft"
    composition.confirmed_by_username = None
    composition.confirmed_at = None
    composition.updated_by_username = operator_username or "operador"
    composition.updated_at = now
    db.flush()


def save_narrative_blocks(
    db: Session,
    *,
    composition: WorkspaceTopicComposition,
    blocks: list[dict],
    analyst_context: str | None,
    operator_username: str | None,
) -> None:
    by_id = {block.id: block for block in composition.narrative_blocks}
    by_key = {block.block_key: block for block in composition.narrative_blocks}
    now = _utcnow()
    for payload in blocks:
        target = None
        try:
            block_id = int(payload.get("id")) if payload.get("id") not in (None, "") else None
        except (TypeError, ValueError):
            block_id = None
        if block_id:
            target = by_id.get(block_id)
        if not target:
            target = by_key.get(str(payload.get("block_key") or ""))
        if not target:
            continue
        target.title = str(payload.get("title") or target.title).strip()[:256] or target.title
        target.body = str(payload.get("body") or "").strip()[:MAX_BLOCK_CHARS] or None
        target.updated_at = now
    composition.analyst_context = str(analyst_context or "").strip()[:MAX_CONTEXT_CHARS] or None
    composition.status = "draft"
    composition.confirmed_by_username = None
    composition.confirmed_at = None
    composition.updated_by_username = operator_username or "operador"
    composition.updated_at = now
    db.flush()


def confirm_topic_composition(
    db: Session,
    *,
    composition: WorkspaceTopicComposition,
    topic: InvestigativeWorkTopic,
    operator_username: str | None,
) -> None:
    nonempty_blocks = [block for block in composition.narrative_blocks if (block.body or "").strip()]
    if not nonempty_blocks:
        raise ValueError("Componha e revise ao menos um bloco narrativo antes de confirmar o tópico.")
    now = _utcnow()
    composition.status = "confirmed"
    composition.confirmed_by_username = operator_username or "operador"
    composition.confirmed_at = now
    composition.updated_by_username = operator_username or "operador"
    composition.updated_at = now
    topic.status = "completed"
    topic.completed_at = now
    topic.updated_at = now
    db.flush()
