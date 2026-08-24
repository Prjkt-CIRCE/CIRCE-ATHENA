from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models.platea import SharedCase
from app.models.reporting import (
    ReportMetadataIndex,
    ReportProduct,
    WorkspaceReportHeader,
    WorkspaceTopicComposition,
    WorkspaceTopicFact,
)
from app.models.workspace import InvestigativeWorkspace, InvestigativeWorkTopic


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_metadata(value: str | None) -> str:
    raw = unicodedata.normalize("NFKD", str(value or ""))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch)).lower()
    return " ".join(re.findall(r"[a-z0-9]+", raw))


def ensure_report_product(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    case: SharedCase,
    header: WorkspaceReportHeader,
    operator_username: str | None,
) -> ReportProduct:
    if header.report_product_id:
        product = db.query(ReportProduct).filter_by(id=header.report_product_id).first()
        if product:
            return product

    product = (
        db.query(ReportProduct)
        .filter(
            ReportProduct.workspace_id == workspace.id,
            ReportProduct.status.in_(["draft", "in_progress"]),
        )
        .order_by(ReportProduct.id.desc())
        .first()
    )
    now = _utcnow()
    if not product:
        product = ReportProduct(
            product_key=f"RPT-{uuid.uuid4().hex.upper()}",
            workspace_id=workspace.id,
            shared_case_id=case.id,
            owner_username=operator_username or header.updated_by_username or "operador",
            product_type=header.report_label or "RELATÓRIO TÉCNICO",
            title=f"{header.report_label or 'Relatório'} — {case.title}",
            status="draft",
            report_number=header.report_number,
            report_date=header.report_date,
            subject=header.subject,
            created_at=now,
            updated_at=now,
        )
        db.add(product)
        db.flush()

    header.report_product_id = product.id
    db.flush()
    return product


def _metadata_pairs(case: SharedCase, header: WorkspaceReportHeader) -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []

    def add(key: str, value: str | None, scope: str) -> None:
        clean = str(value or "").strip()
        if clean:
            pairs.append((key, clean, scope))

    add("case_ref", case.case_ref, "case")
    add("case_title", case.title, "case")
    add("classification", case.classification, "case")
    add("source_unit", case.source_unit, "case")
    add("report_number", header.report_number, "header")
    add("report_date", header.report_date, "header")
    add("subject", header.subject, "header")
    add("origin", header.origin, "header")
    add("distribution", header.distribution, "header")
    add("previous_distribution", header.previous_distribution, "header")

    for line in re.split(r"[\n;]+", header.references_text or ""):
        add("reference", line, "header")
    for line in re.split(r"[\n;]+", header.annexes_text or ""):
        add("annex", line, "header")

    for person in case.persons:
        add("person_name", person.full_name, "case_person")
        add("person_cpf", person.cpf, "case_person")
        add("person_rg", person.rg, "case_person")
        if person.aliases:
            for alias in re.split(r"[,;\n]+", person.aliases):
                add("person_alias", alias, "case_person")

    return pairs


def sync_report_archive(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    case: SharedCase,
    header: WorkspaceReportHeader,
    operator_username: str | None,
) -> ReportProduct:
    product = ensure_report_product(
        db,
        workspace=workspace,
        case=case,
        header=header,
        operator_username=operator_username,
    )
    now = _utcnow()
    product.product_type = header.report_label or "RELATÓRIO TÉCNICO"
    product.title = f"{product.product_type} — {case.title}"
    product.report_number = header.report_number
    product.report_date = header.report_date
    product.subject = header.subject
    product.owner_username = product.owner_username or operator_username or "operador"
    topics = (
        db.query(InvestigativeWorkTopic)
        .filter(InvestigativeWorkTopic.workspace_id == workspace.id)
        .all()
    )
    product_completed = bool(topics) and all(item.status == "completed" for item in topics)
    product.status = "confirmed" if product_completed else "in_progress"
    product.completed_at = now if product_completed else None
    product.updated_at = now

    product.metadata_entries.clear()
    db.flush()
    seen: set[tuple[str, str]] = set()
    for key_type, value, scope in _metadata_pairs(case, header):
        normalized = normalize_metadata(value)
        if not normalized:
            continue
        identity = (key_type, normalized)
        if identity in seen:
            continue
        seen.add(identity)
        product.metadata_entries.append(
            ReportMetadataIndex(
                key_type=key_type,
                value=value,
                normalized_value=normalized,
                source_scope=scope,
                created_at=now,
            )
        )

    # AT06B63_TOPIC_FACT_ARCHIVE_V1
    topic_facts = (
        db.query(WorkspaceTopicFact)
        .join(WorkspaceTopicComposition, WorkspaceTopicComposition.id == WorkspaceTopicFact.composition_id)
        .filter(
            WorkspaceTopicComposition.workspace_id == workspace.id,
            WorkspaceTopicComposition.status == "confirmed",
            WorkspaceTopicFact.status == "confirmed",
        )
        .all()
    )
    fact_key_map = {
        "event_nature": "event_nature",
        "event_date": "event_date",
        "event_location": "event_location",
        "victims": "person_name",
        "persons_mentioned": "person_name",
        "investigation_origin": "investigation_origin",
        "report_scope": "report_scope",
        "event_summary": "event_summary",
    }
    for fact in topic_facts:
        clean_value = str(fact.value or "").strip()
        if not clean_value:
            continue
        key_type = fact_key_map.get(fact.fact_key, f"topic_fact_{fact.fact_key}"[:64])
        normalized = normalize_metadata(clean_value)
        if not normalized:
            continue
        identity = (key_type, normalized)
        if identity in seen:
            continue
        seen.add(identity)
        product.metadata_entries.append(
            ReportMetadataIndex(
                key_type=key_type,
                value=clean_value,
                normalized_value=normalized,
                source_scope="topic_fact",
                created_at=now,
            )
        )
    db.flush()
    return product


def _query_tokens(query: str) -> list[str]:
    normalized = normalize_metadata(query)
    raw = [item for item in normalized.split() if len(item) >= 3]
    stop = {
        "que", "qual", "quais", "relatorio", "relatorios", "referente", "sobre",
        "fiz", "feito", "produzi", "produzido", "meu", "meus", "uma", "uns",
        "para", "com", "dos", "das", "por", "isso", "esse", "essa",
    }
    return [item for item in raw if item not in stop]


def search_report_archive(
    db: Session,
    query: str,
    *,
    owner_username: str | None = None,
    limit: int = 8,
) -> list[tuple[ReportProduct, int]]:
    tokens = _query_tokens(query)
    if not tokens:
        return []

    query_db = db.query(ReportProduct).options(selectinload(ReportProduct.metadata_entries))
    if owner_username:
        query_db = query_db.filter(ReportProduct.owner_username == owner_username)
    products = query_db.order_by(ReportProduct.updated_at.desc()).limit(300).all()

    scored: list[tuple[ReportProduct, int]] = []
    full_query = normalize_metadata(query)
    query_digits = re.sub(r"\D", "", query or "")
    for product in products:
        score = 0
        product_blob = normalize_metadata(
            " ".join([
                product.product_type or "",
                product.title or "",
                product.report_number or "",
                product.report_date or "",
                product.subject or "",
            ])
        )
        values = [entry.normalized_value for entry in product.metadata_entries]
        if len(query_digits) >= 6:
            for entry in product.metadata_entries:
                entry_digits = re.sub(r"\D", "", entry.value or "")
                if query_digits and (query_digits in entry_digits or entry_digits in query_digits):
                    score += 12 if entry.key_type in {"person_cpf", "person_rg", "report_number", "reference"} else 6
        for token in tokens:
            if token in product_blob:
                score += 2
            for entry in product.metadata_entries:
                if token in entry.normalized_value:
                    score += 4 if entry.key_type in {"person_cpf", "person_rg", "report_number", "reference"} else 2
        for value in values:
            if value and len(value) >= 5 and value in full_query:
                score += 6
        if score:
            scored.append((product, score))

    scored.sort(key=lambda item: (item[1], item[0].updated_at), reverse=True)
    return scored[:limit]


def archive_context_text(results: list[tuple[ReportProduct, int]]) -> tuple[str, list[str], list[int]]:
    if not results:
        return "", [], []
    lines = [
        "ACERVO DE PRODUÇÃO DO OPERADOR",
        "Os itens abaixo são produtos persistentes recuperados por metadados do relatório/caso.",
    ]
    sources: list[str] = []
    case_ids: list[int] = []
    for product, score in results:
        marker = f"REPORT:{product.product_key}"
        sources.append(marker)
        case_ids.append(product.shared_case_id)
        metadata = "; ".join(
            f"{entry.key_type}={entry.value}" for entry in product.metadata_entries[:30]
        )
        lines.append(
            f"[{marker}] titulo={product.title}; tipo={product.product_type}; "
            f"numero={product.report_number or 'não informado'}; data={product.report_date or 'não informada'}; "
            f"assunto={product.subject or 'não informado'}; status={product.status}; "
            f"metadados={metadata}"
        )
    return "\n".join(lines), sources, list(dict.fromkeys(case_ids))
