from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models.platea import SharedCase, SharedDocument
from app.models.reporting import WorkspaceReportHeader
from app.models.workspace import InvestigativeWorkspace, InvestigativeWorkTopic
from app.services.report_archive_service import search_report_archive, sync_report_archive
from app.services.report_topic_composition_service import (
    confirm_topic_composition,
    get_or_create_topic_composition,
    save_fact_map,
    store_fact_map,
    store_narrative_blocks,
)


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db: Session = sessionmaker(bind=engine)()
    now = datetime.now(timezone.utc)
    naive = now.replace(tzinfo=None)
    try:
        case = SharedCase(
            case_ref="ATH-SMOKE-B63",
            case_uuid="smoke-b63",
            origin_type="native",
            created_by_username="analista",
            title="Caso Smoke Dos Fatos",
            status="aberto",
            classification="Furto",
            published_by="analista",
            published_at=naive,
            published_version=1,
            last_updated_at=naive,
        )
        db.add(case); db.flush()
        document = SharedDocument(
            shared_case_id=case.id,
            document_ref="BO-1",
            filename="bo.pdf",
            file_type="pdf",
            sha256="a" * 64,
            description="BO",
            intake_bin="documents",
        )
        db.add(document)
        workspace = InvestigativeWorkspace(
            shared_case_id=case.id,
            created_by_username="analista",
            created_at=now,
            updated_at=now,
        )
        db.add(workspace); db.flush()
        header_topic = InvestigativeWorkTopic(
            workspace_id=workspace.id, topic_key="header", title="Cabeçalho",
            purpose="Cabeçalho", topic_type="structured", status="completed", position=0,
            created_by_username="analista", created_at=now, updated_at=now, completed_at=now,
        )
        facts_topic = InvestigativeWorkTopic(
            workspace_id=workspace.id, topic_key="facts", title="Dos fatos / introdução",
            purpose="Contextualizar", topic_type="narrative", status="in_progress", position=1,
            created_by_username="analista", created_at=now, updated_at=now,
        )
        db.add_all([header_topic, facts_topic]); db.flush()
        header = WorkspaceReportHeader(
            workspace_id=workspace.id,
            state_name="ESTADO", secretariat_name="SEC", agency_name="PC",
            directorate_name="DIR", police_unit_name="DEL", section_name="NUC",
            report_label="RELATÓRIO TÉCNICO", report_date="2026-08-23",
            subject="FURTO", review_status="confirmed",
            confirmed_by_username="analista", confirmed_at=now,
            updated_by_username="analista", created_at=now, updated_at=now,
        )
        db.add(header); db.flush()

        composition = get_or_create_topic_composition(
            db, workspace=workspace, work_topic=facts_topic, operator_username="analista"
        )
        store_fact_map(
            db,
            composition=composition,
            resolved_sources=[{
                "source_type": "document",
                "source_key": "ref:BO-1",
                "label": "bo.pdf",
                "snapshot": {},
            }],
            facts=[{
                "fact_key": "event_nature", "label": "Natureza do fato", "value": "Furto qualificado",
                "source_document_id": document.id, "source_label": "bo.pdf", "page": 1,
                "excerpt": "Furto qualificado", "confidence": 0.98, "notes": "", "position": 1,
            }],
            operator_username="analista",
        )
        save_fact_map(
            db, composition=composition, analyst_context="Caso encaminhado ao Núcleo.",
            facts=[{"fact_key": "event_nature", "value": "Furto qualificado", "status": "confirmed"}],
            operator_username="analista",
        )
        store_narrative_blocks(
            db, composition=composition,
            blocks=[{
                "block_key": "event_summary", "title": "Síntese dos fatos",
                "body": "Conforme o registro, apura-se furto qualificado.",
                "position": 0, "fact_keys": ["event_nature"],
            }],
            operator_username="analista",
        )
        confirm_topic_composition(
            db, composition=composition, topic=facts_topic, operator_username="analista"
        )
        sync_report_archive(
            db, workspace=workspace, case=case, header=header, operator_username="analista"
        )
        db.commit()

        assert composition.status == "confirmed"
        assert facts_topic.status == "completed"
        assert composition.sources and composition.facts and composition.narrative_blocks
        results = search_report_archive(db, "furto qualificado", owner_username="analista")
        assert results
        print("AT-06B6.3 SMOKE: OK")
        print("facts=confirmed narrative=blocks provenance=ok archive=topic-fact")
    finally:
        db.close()


if __name__ == "__main__":
    main()
