from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models.platea import (
    SharedCase,
    SharedCaseAnnotation,
    SharedDocument,
    SharedLink,
    SharedPerson,
)
from app.models.reporting import (
    ReportHeaderTemplate,
    WorkspaceReportHeader,
    WorkspaceReportHeaderSource,
    WorkspaceReportHeaderFieldSource,
)
from app.models.workspace import InvestigativeWorkspace, InvestigativeWorkTopic


DEFAULT_HEADER_TEMPLATE_NAME = "PJC-MT · DERF Cuiabá · Núcleo de Inteligência"

DEFAULT_HEADER_VALUES = {
    "state_name": "ESTADO DE MATO GROSSO",
    "secretariat_name": "SECRETARIA DE ESTADO DE SEGURANÇA PÚBLICA",
    "agency_name": "POLÍCIA CIVIL",
    "directorate_name": "DIRETORIA METROPOLITANA",
    "police_unit_name": "DELEGACIA ESPECIALIZADA EM REPRESSÃO A ROUBOS E FURTOS DE CUIABÁ",
    "section_name": "NÚCLEO DE INTELIGÊNCIA",
    "report_label": "RELATÓRIO TÉCNICO",
}

HEADER_TEXT_LIMITS = {
    "state_name": 256,
    "secretariat_name": 256,
    "agency_name": 256,
    "directorate_name": 256,
    "police_unit_name": 512,
    "section_name": 256,
    "report_label": 128,
    "report_number": 128,
    "report_date": 16,
    "subject": 512,
    "origin": 512,
    "distribution": 512,
    "previous_distribution": 512,
    "references_text": 4000,
    "annexes_text": 4000,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value, limit: int) -> str:
    return str(value or "").strip()[:limit]


def ensure_default_header_template(
    db: Session,
    *,
    operator_username: str | None,
) -> ReportHeaderTemplate:
    template = (
        db.query(ReportHeaderTemplate)
        .filter(ReportHeaderTemplate.is_default.is_(True))
        .order_by(ReportHeaderTemplate.id)
        .first()
    )
    if template:
        return template

    template = db.query(ReportHeaderTemplate).order_by(ReportHeaderTemplate.id).first()
    if template:
        template.is_default = True
        template.updated_at = _utcnow()
        db.flush()
        return template

    template = ReportHeaderTemplate(
        name=DEFAULT_HEADER_TEMPLATE_NAME,
        is_default=True,
        **DEFAULT_HEADER_VALUES,
        created_by_username=operator_username or "operador",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(template)
    db.flush()
    return template


def list_header_templates(db: Session) -> list[ReportHeaderTemplate]:
    return (
        db.query(ReportHeaderTemplate)
        .order_by(ReportHeaderTemplate.is_default.desc(), ReportHeaderTemplate.name, ReportHeaderTemplate.id)
        .all()
    )


def get_or_create_workspace_header(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    case: SharedCase,
    operator_username: str | None,
) -> WorkspaceReportHeader:
    existing = (
        db.query(WorkspaceReportHeader)
        .options(
            selectinload(WorkspaceReportHeader.sources),
            selectinload(WorkspaceReportHeader.field_sources),
        )
        .filter(WorkspaceReportHeader.workspace_id == workspace.id)
        .first()
    )
    if existing:
        return existing

    template = ensure_default_header_template(db, operator_username=operator_username)
    header = WorkspaceReportHeader(
        workspace_id=workspace.id,
        template_id=template.id,
        state_name=template.state_name,
        secretariat_name=template.secretariat_name,
        agency_name=template.agency_name,
        directorate_name=template.directorate_name,
        police_unit_name=template.police_unit_name,
        section_name=template.section_name,
        report_label=template.report_label,
        report_number=None,
        report_date=date.today().isoformat(),
        subject=None,
        origin=None,
        distribution=None,
        previous_distribution=None,
        references_text=None,
        annexes_text=None,
        review_status="draft",
        confirmed_by_username=None,
        confirmed_at=None,
        updated_by_username=operator_username or "operador",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(header)
    db.flush()
    return header


def header_source_tokens(header: WorkspaceReportHeader) -> list[str]:
    return [f"{item.source_type}:{item.source_key}" for item in header.sources]


def header_template_payload(template: ReportHeaderTemplate) -> dict:
    return {
        "id": template.id,
        "name": template.name,
        "is_default": bool(template.is_default),
        "state_name": template.state_name,
        "secretariat_name": template.secretariat_name,
        "agency_name": template.agency_name,
        "directorate_name": template.directorate_name,
        "police_unit_name": template.police_unit_name,
        "section_name": template.section_name,
        "report_label": template.report_label,
    }


def header_payload(header: WorkspaceReportHeader) -> dict:
    return {
        "id": header.id,
        "workspace_id": header.workspace_id,
        "template_id": header.template_id,
        "state_name": header.state_name,
        "secretariat_name": header.secretariat_name,
        "agency_name": header.agency_name,
        "directorate_name": header.directorate_name,
        "police_unit_name": header.police_unit_name,
        "section_name": header.section_name,
        "report_label": header.report_label,
        "report_number": header.report_number or "",
        "report_date": header.report_date or "",
        "subject": header.subject or "",
        "origin": header.origin or "",
        "distribution": header.distribution or "",
        "previous_distribution": header.previous_distribution or "",
        "references_text": header.references_text or "",
        "annexes_text": header.annexes_text or "",
        "review_status": header.review_status or "draft",
        "confirmed_by_username": header.confirmed_by_username or "",
        "confirmed_at": header.confirmed_at.isoformat() if header.confirmed_at else "",
        "source_tokens": header_source_tokens(header),
    }


def _resolve_source(
    db: Session,
    *,
    case_id: int,
    token: str,
) -> tuple[str, str, str] | None:
    try:
        source_type, source_key = token.split(":", 1)
    except ValueError:
        return None

    source_type = source_type.strip().lower()
    source_key = source_key.strip()
    if not source_key:
        return None

    try:
        numeric_id = int(source_key)
    except ValueError:
        return None

    if source_type == "document":
        item = (
            db.query(SharedDocument)
            .filter(SharedDocument.id == numeric_id, SharedDocument.shared_case_id == case_id)
            .first()
        )
        if item:
            return source_type, source_key, item.filename
    elif source_type == "person":
        item = (
            db.query(SharedPerson)
            .filter(SharedPerson.id == numeric_id, SharedPerson.shared_case_id == case_id)
            .first()
        )
        if item:
            return source_type, source_key, item.full_name
    elif source_type == "link":
        item = (
            db.query(SharedLink)
            .filter(SharedLink.id == numeric_id, SharedLink.shared_case_id == case_id)
            .first()
        )
        if item:
            label = f"{item.entity_a_name or item.entity_a_ref} → {item.entity_b_name or item.entity_b_ref}"
            return source_type, source_key, label
    elif source_type == "annotation":
        item = (
            db.query(SharedCaseAnnotation)
            .filter(SharedCaseAnnotation.id == numeric_id, SharedCaseAnnotation.shared_case_id == case_id)
            .first()
        )
        if item:
            return source_type, source_key, item.content[:200]
    return None


def update_workspace_header(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    case: SharedCase,
    payload: dict,
    source_tokens: list[str],
    operator_username: str | None,
) -> WorkspaceReportHeader:
    header = get_or_create_workspace_header(
        db,
        workspace=workspace,
        case=case,
        operator_username=operator_username,
    )

    template_id = payload.get("template_id")
    try:
        template_id = int(template_id) if template_id not in (None, "") else None
    except (TypeError, ValueError):
        template_id = None

    if template_id:
        template = db.query(ReportHeaderTemplate).filter_by(id=template_id).first()
        if template:
            header.template_id = template.id

    for field, limit in HEADER_TEXT_LIMITS.items():
        setattr(header, field, _clean(payload.get(field), limit) or None)

    # Campos institucionais e rótulo não podem ficar nulos.
    for field in (
        "state_name",
        "secretariat_name",
        "agency_name",
        "directorate_name",
        "police_unit_name",
        "section_name",
        "report_label",
    ):
        if not getattr(header, field):
            setattr(header, field, DEFAULT_HEADER_VALUES[field])

    resolved: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for token in source_tokens:
        source = _resolve_source(db, case_id=case.id, token=token)
        if not source:
            continue
        identity = (source[0], source[1])
        if identity in seen:
            continue
        seen.add(identity)
        resolved.append(source)

    header.sources.clear()
    db.flush()
    for source_type, source_key, label in resolved:
        header.sources.append(
            WorkspaceReportHeaderSource(
                source_type=source_type,
                source_key=source_key,
                source_label_snapshot=label[:512],
            )
        )

    header.review_status = "draft"
    header.confirmed_by_username = None
    header.confirmed_at = None
    header.updated_by_username = operator_username or "operador"
    header.updated_at = _utcnow()

    # A proposta de extração continua auditável. Se o valor salvo coincide com a
    # proposta, ela é marcada como aceita; caso contrário, rejeitada/corrigida.
    for item in header.field_sources:
        if item.status != "proposed":
            continue
        saved_value = str(getattr(header, item.field_name, None) or "").strip()
        proposed_value = str(item.extracted_value or "").strip()
        item.status = "accepted" if saved_value and saved_value == proposed_value else "rejected"

    topic = (
        db.query(InvestigativeWorkTopic)
        .filter(
            InvestigativeWorkTopic.workspace_id == workspace.id,
            InvestigativeWorkTopic.topic_key == "header",
        )
        .first()
    )
    if topic and topic.status in {"pending", "review", "completed"}:
        topic.status = "in_progress"
        topic.updated_at = _utcnow()

    workspace.updated_at = _utcnow()
    db.flush()
    return header


def create_header_template(
    db: Session,
    *,
    name: str,
    payload: dict,
    operator_username: str | None,
    make_default: bool = False,
) -> ReportHeaderTemplate:
    clean_name = _clean(name, 256)
    if len(clean_name) < 3:
        raise ValueError("Informe um nome para o novo template.")

    values = {}
    for field in (
        "state_name",
        "secretariat_name",
        "agency_name",
        "directorate_name",
        "police_unit_name",
        "section_name",
        "report_label",
    ):
        values[field] = _clean(payload.get(field), HEADER_TEXT_LIMITS[field]) or DEFAULT_HEADER_VALUES[field]

    if make_default:
        db.query(ReportHeaderTemplate).update(
            {ReportHeaderTemplate.is_default: False},
            synchronize_session=False,
        )

    template = ReportHeaderTemplate(
        name=clean_name,
        is_default=bool(make_default),
        **values,
        created_by_username=operator_username or "operador",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(template)
    db.flush()
    return template


def confirm_workspace_header(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    case: SharedCase,
    payload: dict,
    source_tokens: list[str],
    operator_username: str | None,
) -> WorkspaceReportHeader:
    header = update_workspace_header(
        db,
        workspace=workspace,
        case=case,
        payload=payload,
        source_tokens=source_tokens,
        operator_username=operator_username,
    )
    now = _utcnow()
    header.review_status = "confirmed"
    header.confirmed_by_username = operator_username or "operador"
    header.confirmed_at = now
    header.updated_at = now

    for item in header.field_sources:
        if item.status == "proposed":
            saved_value = str(getattr(header, item.field_name, None) or "").strip()
            proposed_value = str(item.extracted_value or "").strip()
            item.status = "accepted" if saved_value and saved_value == proposed_value else "rejected"

    topic = (
        db.query(InvestigativeWorkTopic)
        .filter(
            InvestigativeWorkTopic.workspace_id == workspace.id,
            InvestigativeWorkTopic.topic_key == "header",
        )
        .first()
    )
    if topic:
        topic.status = "completed"
        topic.updated_at = now
    workspace.updated_at = now
    db.flush()
    return header
