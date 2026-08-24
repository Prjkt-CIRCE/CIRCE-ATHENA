from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.platea import SharedDocument
from app.models.reporting import WorkspaceReportHeader, WorkspaceReportHeaderFieldSource
from app.models.workspace import InvestigativeWorkTopic
from app.services.case_intake_service import resolve_document_storage_path

HEADER_FIELDS = (
    "subject",
    "origin",
    "distribution",
    "previous_distribution",
    "references_text",
    "annexes_text",
)
MAX_PAGES_PER_DOCUMENT = 14
MAX_PAGE_CHARS = 5000
MAX_TOTAL_CHARS = 70000


@dataclass
class PdfPageText:
    document_id: int
    filename: str
    page_number: int
    text: str


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


def _pdf_reader():
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "A extração de PDF requer o pacote pypdf. Execute o instalador AT-06B6 novamente."
        ) from exc
    return PdfReader


def extract_pdf_pages(document: SharedDocument) -> tuple[list[PdfPageText], list[str]]:
    path = resolve_document_storage_path(document)
    if not path:
        return [], [f"{document.filename}: original local indisponível."]
    if Path(path).suffix.lower() != ".pdf" and (document.mime_type or "").lower() != "application/pdf":
        return [], [f"{document.filename}: não é PDF nesta etapa de extração."]

    PdfReader = _pdf_reader()
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        return [], [f"{document.filename}: não foi possível abrir o PDF ({exc})."]

    pages: list[PdfPageText] = []
    warnings: list[str] = []
    for index, page in enumerate(reader.pages[:MAX_PAGES_PER_DOCUMENT], start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        if text:
            pages.append(
                PdfPageText(
                    document_id=document.id,
                    filename=document.filename,
                    page_number=index,
                    text=text[:MAX_PAGE_CHARS],
                )
            )
    if not pages:
        warnings.append(
            f"{document.filename}: nenhuma camada textual detectada; OCR será necessário em etapa posterior."
        )
    elif len(reader.pages) > MAX_PAGES_PER_DOCUMENT:
        warnings.append(
            f"{document.filename}: para o cabeçalho foram lidas as primeiras {MAX_PAGES_PER_DOCUMENT} páginas."
        )
    return pages, warnings


def _build_prompt(pages: list[PdfPageText]) -> str:
    blocks: list[str] = []
    used = 0
    for page in pages:
        block = (
            f"\n--- DOCUMENTO_ID={page.document_id} | ARQUIVO={page.filename} | PAGINA={page.page_number} ---\n"
            f"{page.text}\n"
        )
        if used + len(block) > MAX_TOTAL_CHARS:
            break
        used += len(block)
        blocks.append(block)

    schema = {
        field: {
            "value": "",
            "source_document_id": None,
            "page": None,
            "excerpt": "",
            "confidence": 0.0,
        }
        for field in HEADER_FIELDS
    }
    return (
        "Você está preenchendo o CABEÇALHO de um relatório policial a partir de documentos reais. "
        "Extraia somente informação explicitamente sustentada pelo material fornecido. Não invente. "
        "O número do relatório e a data do relatório NÃO são objeto desta extração. "
        "Campos: subject=ASSUNTO; origin=ORIGEM; distribution=DIFUSÃO; "
        "previous_distribution=DIFUSÃO ANTERIOR; references_text=REFERÊNCIAS; annexes_text=ANEXOS. "
        "Para REFERÊNCIAS consolide, quando expressamente presentes, números de B.O., O.S., I.P./Inquérito, "
        "processo/medida judicial e outras referências institucionais. Preserve a identificação e o número. "
        "Se um campo não constar, devolva value vazio e source_document_id/page nulos. "
        "source_document_id DEVE ser um DOCUMENTO_ID fornecido. page deve ser a página que sustenta o valor. "
        "excerpt deve ser um trecho curto e fiel da fonte, sem inventar citação. confidence entre 0 e 1. "
        "Retorne SOMENTE JSON válido, sem markdown, exatamente no formato: "
        f"{{\"fields\": {json.dumps(schema, ensure_ascii=False)}, \"notes\": []}}.\n"
        "MATERIAL:" + "".join(blocks)
    )


def _clean_candidate(field_name: str, raw: object, valid_documents: dict[int, SharedDocument]) -> dict:
    item = raw if isinstance(raw, dict) else {}
    value = str(item.get("value") or "").strip()
    source_id = item.get("source_document_id")
    try:
        source_id = int(source_id) if source_id not in (None, "") else None
    except (TypeError, ValueError):
        source_id = None
    if source_id not in valid_documents:
        source_id = None
    try:
        page = int(item.get("page")) if item.get("page") not in (None, "") else None
    except (TypeError, ValueError):
        page = None
    try:
        confidence = float(item.get("confidence"))
    except (TypeError, ValueError):
        confidence = None
    if confidence is not None:
        confidence = max(0.0, min(1.0, confidence))
    excerpt = str(item.get("excerpt") or "").strip()[:1200]
    document = valid_documents.get(source_id) if source_id else None
    return {
        "field_name": field_name,
        "value": value[:4000],
        "source_document_id": source_id,
        "source_label": document.filename if document else None,
        "page": page,
        "excerpt": excerpt,
        "confidence": confidence,
    }


async def propose_header_extraction(
    *,
    documents: list[SharedDocument],
) -> tuple[dict[str, dict], list[str], list[str]]:
    pages: list[PdfPageText] = []
    warnings: list[str] = []
    for document in documents:
        extracted, item_warnings = extract_pdf_pages(document)
        pages.extend(extracted)
        warnings.extend(item_warnings)

    if not pages:
        raise ValueError(
            "Nenhum texto de PDF pôde ser extraído das fontes selecionadas. "
            "Se os arquivos forem digitalizados como imagem, será necessário OCR."
        )

    prompt = _build_prompt(pages)
    async with httpx.AsyncClient(timeout=150.0) as client:
        response = await client.post(
            f"{settings.llm_base_url}/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é Athena, assistente local de inteligência policial. "
                            "Nesta tarefa você apenas extrai dados estruturados com proveniência; "
                            "não toma decisões investigativas e não preenche lacunas por suposição."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": 2200,
            },
            headers={"Authorization": "Bearer lm-studio"},
        )
        response.raise_for_status()

    data = response.json()
    message = data["choices"][0]["message"]
    raw = message.get("content") or ""
    if not raw:
        raise ValueError("Athena não retornou conteúdo final para a extração.")
    parsed = _extract_json_object(raw)
    raw_fields = parsed.get("fields") if isinstance(parsed.get("fields"), dict) else {}
    valid_documents = {item.id: item for item in documents}
    fields = {
        field: _clean_candidate(field, raw_fields.get(field), valid_documents)
        for field in HEADER_FIELDS
    }
    notes = parsed.get("notes") if isinstance(parsed.get("notes"), list) else []
    clean_notes = [str(item).strip()[:500] for item in notes if str(item).strip()][:12]
    return fields, warnings, clean_notes


def store_header_extraction(
    db: Session,
    *,
    header: WorkspaceReportHeader,
    fields: dict[str, dict],
) -> None:
    db.query(WorkspaceReportHeaderFieldSource).filter(
        WorkspaceReportHeaderFieldSource.report_header_id == header.id,
        WorkspaceReportHeaderFieldSource.status == "proposed",
    ).delete(synchronize_session=False)
    now = _utcnow()
    for field_name, candidate in fields.items():
        if field_name not in HEADER_FIELDS:
            continue
        db.add(
            WorkspaceReportHeaderFieldSource(
                report_header_id=header.id,
                field_name=field_name,
                extracted_value=candidate.get("value") or None,
                source_document_id=candidate.get("source_document_id"),
                source_label_snapshot=candidate.get("source_label"),
                page_number=candidate.get("page"),
                excerpt=candidate.get("excerpt") or None,
                confidence=candidate.get("confidence"),
                extraction_method="llm_pdf_text",
                status="proposed",
                created_at=now,
            )
        )
    header.review_status = "proposed"
    header.confirmed_by_username = None
    header.confirmed_at = None
    header.updated_at = now
    topic = (
        db.query(InvestigativeWorkTopic)
        .filter(
            InvestigativeWorkTopic.workspace_id == header.workspace_id,
            InvestigativeWorkTopic.topic_key == "header",
        )
        .first()
    )
    if topic:
        topic.status = "in_progress"
        topic.updated_at = now
    db.flush()


def field_sources_payload(header: WorkspaceReportHeader) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in header.field_sources:
        if item.status not in {"proposed", "accepted"}:
            continue
        result[item.field_name] = {
            "value": item.extracted_value or "",
            "source_document_id": item.source_document_id,
            "source_label": item.source_label_snapshot or "",
            "page": item.page_number,
            "excerpt": item.excerpt or "",
            "confidence": item.confidence,
            "status": item.status,
        }
    return result
