from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.platea import SharedCase, SharedDocument
from app.models.reporting import (
    ReportHeaderTemplate,
    WorkspaceReportHeader,
    WorkspaceReportHeaderSource,
)
from app.models.workspace import InvestigativeWorkspace
from app.services.report_header_service import (
    create_header_template,
    ensure_default_header_template,
    get_or_create_workspace_header,
    header_payload,
    update_workspace_header,
)


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime.utcnow()
    case = SharedCase(
        case_ref="ATH-B52-SMOKE",
        case_uuid="b52-smoke",
        origin_type="native",
        created_by_operator_id=1,
        created_by_username="smoke",
        title="Caso Smoke",
        status="aberto",
        classification="furto",
        notes=None,
        source_unit="Núcleo",
        published_by="smoke",
        published_at=now,
        published_version=1,
        last_updated_at=now,
    )
    db.add(case)
    db.flush()

    workspace = InvestigativeWorkspace(
        shared_case_id=case.id,
        created_by_operator_id=1,
        created_by_username="smoke",
    )
    db.add(workspace)
    db.flush()

    document = SharedDocument(
        shared_case_id=case.id,
        document_ref="DOC-SMOKE",
        filename="ordem_servico.pdf",
        file_type="pdf",
        sha256="a" * 64,
        description="OS",
        intake_bin="documents",
        origin="native_intake",
    )
    db.add(document)
    db.flush()

    default_template = ensure_default_header_template(db, operator_username="smoke")
    assert default_template.state_name == "ESTADO DE MATO GROSSO"

    header = get_or_create_workspace_header(
        db,
        workspace=workspace,
        case=case,
        operator_username="smoke",
    )
    assert header.workspace_id == workspace.id
    assert header.report_number is None

    header = update_workspace_header(
        db,
        workspace=workspace,
        case=case,
        payload={
            "template_id": default_template.id,
            "state_name": default_template.state_name,
            "secretariat_name": default_template.secretariat_name,
            "agency_name": default_template.agency_name,
            "directorate_name": default_template.directorate_name,
            "police_unit_name": default_template.police_unit_name,
            "section_name": default_template.section_name,
            "report_label": "RELATÓRIO TÉCNICO",
            "report_number": "",
            "report_date": "2026-08-22",
            "subject": "FURTO QUALIFICADO",
            "origin": "NÚCLEO DE INTELIGÊNCIA",
            "distribution": "XXX",
            "previous_distribution": "",
            "references_text": "B.O. nº 2025.11644",
            "annexes_text": "",
        },
        source_tokens=[f"document:{document.id}"],
        operator_username="smoke",
    )
    assert len(header.sources) == 1
    assert header.subject == "FURTO QUALIFICADO"

    new_template = create_header_template(
        db,
        name="Template Smoke",
        payload=header_payload(header),
        operator_username="smoke",
    )
    assert new_template.name == "Template Smoke"

    db.commit()

    assert db.query(ReportHeaderTemplate).count() == 2
    assert db.query(WorkspaceReportHeader).count() == 1
    assert db.query(WorkspaceReportHeaderSource).count() == 1

    print("AT-06B5.2 SMOKE: OK")
    print("header=ok template=ok source=ok")


if __name__ == "__main__":
    main()
