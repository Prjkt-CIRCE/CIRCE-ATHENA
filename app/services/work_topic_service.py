from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.workspace import InvestigativeWorkTopic, InvestigativeWorkspace

TOPIC_STATUSES = {"pending", "in_progress", "review", "completed"}

MOBILE_ANALYSIS_TOPICS = [
    ("header", "Cabeçalho", "Consolidar metadados institucionais, referências, anexos e numeração do produto.", "structured"),
    ("facts", "Dos fatos / introdução", "Contextualizar a investigação e delimitar o objetivo da análise.", "narrative"),
    ("analysis_objects", "Objetos de análise", "Identificar e descrever aparelhos, extrações, IMEIs, SIMs, lacres, laudos e autorização judicial.", "structured"),
    ("qualifications", "Qualificação dos envolvidos", "Consolidar qualificação, fotografia e breve contexto investigativo das pessoas relevantes.", "structured"),
    ("images", "Análise de imagens", "Organizar imagens relevantes, metadados, correlações e observações do analista.", "analytical"),
    ("conversations", "Análise de conversações", "Organizar interlocutores, sequências, recortes, resumos e achados relevantes.", "analytical"),
    ("considerations", "Considerações finais", "Reorganizar os achados validados de forma sintética e coerente com a cronologia e os temas.", "synthesis"),
    ("conclusion", "Conclusão", "Sintetizar exclusivamente achados validados, distinguindo fatos, inferências e limitações.", "synthesis"),
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_work_topics(db: Session, workspace_id: int) -> list[InvestigativeWorkTopic]:
    return (
        db.query(InvestigativeWorkTopic)
        .filter(InvestigativeWorkTopic.workspace_id == workspace_id)
        .order_by(InvestigativeWorkTopic.position, InvestigativeWorkTopic.id)
        .all()
    )


def bootstrap_mobile_analysis_topics(
    db: Session,
    *,
    workspace: InvestigativeWorkspace,
    operator_id: int | None,
    operator_username: str | None,
) -> tuple[list[InvestigativeWorkTopic], bool]:
    existing = list_work_topics(db, workspace.id)
    if existing:
        return existing, False

    now = _utcnow()
    created: list[InvestigativeWorkTopic] = []
    for position, (key, title, purpose, topic_type) in enumerate(MOBILE_ANALYSIS_TOPICS):
        item = InvestigativeWorkTopic(
            workspace_id=workspace.id,
            topic_key=key,
            title=title,
            purpose=purpose,
            topic_type=topic_type,
            status="pending",
            position=position,
            created_by_operator_id=operator_id,
            created_by_username=operator_username or "operador",
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        created.append(item)
    db.flush()
    workspace.updated_at = now
    return created, True


def get_work_topic(db: Session, *, workspace_id: int, topic_id: int) -> InvestigativeWorkTopic | None:
    return (
        db.query(InvestigativeWorkTopic)
        .filter(
            InvestigativeWorkTopic.id == topic_id,
            InvestigativeWorkTopic.workspace_id == workspace_id,
        )
        .first()
    )


def choose_active_topic(topics: list[InvestigativeWorkTopic], requested_id: int | None) -> InvestigativeWorkTopic | None:
    if requested_id is not None:
        match = next((item for item in topics if item.id == requested_id), None)
        if match:
            return match
    return (
        next((item for item in topics if item.status == "in_progress"), None)
        or next((item for item in topics if item.status == "review"), None)
        or next((item for item in topics if item.status == "pending"), None)
        or (topics[0] if topics else None)
    )


def update_work_topic_status(
    db: Session,
    *,
    workspace_id: int,
    topic_id: int,
    status: str,
) -> tuple[InvestigativeWorkTopic | None, str | None]:
    clean = (status or "").strip().lower()
    if clean not in TOPIC_STATUSES:
        return None, "Estado de tópico inválido."

    topic = get_work_topic(db, workspace_id=workspace_id, topic_id=topic_id)
    if not topic:
        return None, "Tópico de trabalho não encontrado."

    now = _utcnow()
    topic.status = clean
    topic.updated_at = now
    topic.completed_at = now if clean == "completed" else None
    workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
    if workspace:
        workspace.updated_at = now
    db.flush()
    return topic, None


def next_incomplete_topic(topics: list[InvestigativeWorkTopic], current_id: int) -> InvestigativeWorkTopic | None:
    ordered = list(topics)
    try:
        index = next(i for i, item in enumerate(ordered) if item.id == current_id)
    except StopIteration:
        return None
    for item in ordered[index + 1:]:
        if item.status != "completed":
            return item
    for item in ordered[:index]:
        if item.status != "completed":
            return item
    return None
