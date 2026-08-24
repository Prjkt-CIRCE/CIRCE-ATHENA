"""AT-06A smoke test — Workspace core sem tocar no banco operacional."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.operator import Operator  # noqa: F401
from app.models.platea import SharedCase, SharedDocument, SharedPerson  # noqa: F401
from app.models.workspace import InvestigativeWorkspace  # noqa: F401
from app.services.assistant_context_service import build_investigative_context
from app.services.investigative_analysis_service import (
    AnalysisProposal,
    create_excerpt_draft,
    discard_excerpt,
    list_excerpt_drafts,
    list_findings,
    resolve_excerpt_sources,
    validate_finding,
)

from app.services.work_topic_service import (
    bootstrap_mobile_analysis_topics,
    update_work_topic_status,
)
from app.services.workspace_service import (
    add_block_sources,
    build_block_context,
    create_block,
    discard_block,
    list_blocks,
    open_workspace,
    remove_block_source,
)


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    case = SharedCase(
        case_ref="AT06A-SMOKE",
        title="Caso de teste AT-06A",
        status="aberto",
        published_by="smoke",
        published_at=__import__("datetime").datetime.now(),
        published_version=1,
    )
    db.add(case)
    db.flush()
    person = SharedPerson(
        shared_case_id=case.id,
        person_ref="P-001",
        full_name="Pessoa Teste",
    )
    document = SharedDocument(
        shared_case_id=case.id,
        document_ref="D-001",
        filename="documento_teste.pdf",
        sha256="a" * 64,
    )
    db.add_all([person, document])
    db.commit()

    workspace, created = open_workspace(
        db,
        case_ref=case.case_ref,
        operator_id=1,
        operator_username="smoke",
    )
    assert workspace is not None and created is True
    same_workspace, created_again = open_workspace(
        db,
        case_ref=case.case_ref,
        operator_id=1,
        operator_username="smoke",
    )
    assert same_workspace.id == workspace.id and created_again is False

    block, error = create_block(
        db,
        workspace_id=workspace.id,
        title="Vínculo inicial",
        summary="Bloco de validação do núcleo.",
        source_tokens=[f"person:{person.id}"],
        operator_id=1,
        operator_username="smoke",
    )
    assert error is None and block is not None
    db.commit()

    # AT06A_POOL_DND_V1 — simula drop de documento em bloco existente.
    block, added, add_error = add_block_sources(
        db,
        workspace_id=workspace.id,
        block_id=block.id,
        source_tokens=[f"document:{document.id}"],
    )
    assert add_error is None and block is not None and len(added) == 1
    db.commit()

    block, duplicate_added, duplicate_error = add_block_sources(
        db,
        workspace_id=workspace.id,
        block_id=block.id,
        source_tokens=[f"document:{document.id}"],
    )
    assert duplicate_error is None and duplicate_added == []
    db.commit()

    context = build_block_context(db, case_ref=case.case_ref, block_id=block.id)
    assert context is not None
    assert "Pessoa Teste" in context.text
    assert "documento_teste.pdf" in context.text
    assert "BLOCO:" in context.sources[0]

    # AT06A_UNDO_V1
    source_to_remove = next(item for item in block.sources if item.source_type == "document")
    removed, remove_error = remove_block_source(
        db,
        workspace_id=workspace.id,
        block_id=block.id,
        source_id=source_to_remove.id,
    )
    assert remove_error is None and removed is not None
    db.commit()

    remaining = list_blocks(db, workspace.id)
    assert len(remaining) == 1
    assert len(remaining[0].sources) == 1

    discarded, discard_error = discard_block(
        db,
        workspace_id=workspace.id,
        block_id=block.id,
    )
    assert discard_error is None and discarded is not None
    db.commit()
    assert discarded.status == "discarded"
    assert list_blocks(db, workspace.id) == []
    assert build_block_context(db, case_ref=case.case_ref, block_id=block.id) is None

    topics, created_topics = bootstrap_mobile_analysis_topics(
        db, workspace=workspace, operator_id=None, operator_username="smoke"
    )
    assert created_topics is True and len(topics) >= 6
    topic = topics[2]
    topic, topic_error = update_work_topic_status(
        db, workspace_id=workspace.id, topic_id=topic.id, status="in_progress"
    )
    assert topic_error is None and topic is not None and topic.status == "in_progress"
    db.commit()

    # AT06B1_ANALYTICAL_CORE_V1 — recorte -> proposta -> validação humana -> achado.
    workspace_ref, case_ref, excerpt_sources, excerpt_error = resolve_excerpt_sources(
        db,
        workspace_id=workspace.id,
        source_tokens=[f"person:{person.id}", f"document:{document.id}"],
    )
    assert excerpt_error is None and workspace_ref is not None and case_ref is not None
    assert len(excerpt_sources) == 2

    proposal = AnalysisProposal(
        title="Relação a validar",
        objective_summary="Pessoa e documento selecionados formam o recorte de teste.",
        interpretation="A relação ainda depende de validação humana.",
        suggested_type="inference",
        support_gaps=["Smoke não realiza inferência de conteúdo."],
    )
    excerpt = create_excerpt_draft(
        db,
        workspace=workspace_ref,
        analyst_note="Nota literal do analista para o smoke.",
        sources=excerpt_sources,
        proposal=proposal,
        operator_id=1,
        operator_username="smoke",
        work_topic_id=topic.id,
    )
    db.commit()
    assert excerpt.status == "draft" and excerpt.work_topic_id == topic.id and len(excerpt.sources) == 2
    assert len(list_excerpt_drafts(db, workspace.id)) == 1

    finding, finding_error = validate_finding(
        db,
        workspace_id=workspace.id,
        excerpt_id=excerpt.id,
        title=excerpt.title,
        objective_summary=excerpt.proposed_summary,
        interpretation=excerpt.proposed_interpretation,
        finding_type="inference",
        operator_id=1,
        operator_username="smoke",
    )
    assert finding_error is None and finding is not None
    db.commit()
    assert finding.status == "validated" and finding.finding_type == "inference"
    assert finding.work_topic_id == topic.id
    assert list_excerpt_drafts(db, workspace.id) == []
    assert len(list_findings(db, workspace.id)) == 1

    assistant_context = build_investigative_context(
        db,
        "Quais são os achados deste caso?",
        active_case_ref=case.case_ref,
    )
    assert f"ACHADO:{finding.id}" in assistant_context.sources
    assert "Inferência" not in assistant_context.text or "tipo=inference" in assistant_context.text

    second_excerpt = create_excerpt_draft(
        db,
        workspace=workspace_ref,
        analyst_note="Recorte descartável.",
        sources=excerpt_sources[:1],
        proposal=AnalysisProposal(
            title="Descartar",
            objective_summary="Recorte temporário.",
            interpretation="",
            suggested_type="annotation",
            support_gaps=[],
        ),
        operator_id=1,
        operator_username="smoke",
        work_topic_id=topic.id,
    )
    db.commit()
    discarded_excerpt, discard_excerpt_error = discard_excerpt(
        db,
        workspace_id=workspace.id,
        excerpt_id=second_excerpt.id,
    )
    assert discard_excerpt_error is None and discarded_excerpt is not None
    db.commit()
    assert discarded_excerpt.status == "discarded"

    print("AT-06B2 SMOKE: OK")
    print(f"workspace={workspace.id} block={block.id} undo=ok pool_dnd=ok excerpt=ok finding=ok topics=ok")


if __name__ == "__main__":
    main()
