from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models.platea import SharedCase, SharedPerson
from app.models.reporting import WorkspaceReportHeader
from app.models.workspace import InvestigativeWorkspace
from app.services.report_archive_service import search_report_archive, sync_report_archive
from app.services.assistant_context_service import build_investigative_context


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db: Session = sessionmaker(bind=engine)()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        case = SharedCase(
            case_ref="ATH-SMOKE-B6",
            case_uuid="smoke-b6-case",
            origin_type="native",
            created_by_username="analista",
            title="Operação Acervo",
            status="aberto",
            classification="Latrocínio",
            source_unit="Núcleo de Inteligência",
            published_by="analista",
            published_at=now,
            published_version=1,
            last_updated_at=now,
        )
        db.add(case); db.flush()
        db.add(SharedPerson(
            shared_case_id=case.id,
            person_ref="P1",
            full_name="Fulano de Tal",
            cpf="123.456.789-00",
            role_in_case="suspeito",
        ))
        workspace = InvestigativeWorkspace(
            shared_case_id=case.id,
            created_by_username="analista",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(workspace); db.flush()
        header = WorkspaceReportHeader(
            workspace_id=workspace.id,
            state_name="ESTADO DE MATO GROSSO",
            secretariat_name="SESP",
            agency_name="POLÍCIA CIVIL",
            directorate_name="DIRETORIA",
            police_unit_name="DELEGACIA",
            section_name="NÚCLEO",
            report_label="RELATÓRIO TÉCNICO",
            report_number="2026.13.0001",
            report_date="2026-08-23",
            subject="LATROCÍNIO",
            origin="NÚCLEO DE INTELIGÊNCIA",
            distribution="XXX",
            previous_distribution=None,
            references_text="I.P. 212.4.2026.9999; B.O. 2026.12345",
            annexes_text=None,
            review_status="confirmed",
            confirmed_by_username="analista",
            confirmed_at=datetime.now(timezone.utc),
            updated_by_username="analista",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(header); db.flush()
        sync_report_archive(
            db, workspace=workspace, case=case, header=header,
            operator_username="analista",
        )
        db.commit()

        by_ip = search_report_archive(db, "qual relatório fiz sobre 212.4.2026.9999", owner_username="analista")
        by_cpf = search_report_archive(db, "12345678900", owner_username="analista")
        by_name = search_report_archive(db, "Fulano de Tal", owner_username="analista")
        assert by_ip and by_cpf and by_name
        assert header.report_product_id is not None
        ctx = build_investigative_context(
            db,
            "que relatório eu fiz referente ao CPF 123.456.789-00?",
            operator_username="analista",
        )
        assert "ACERVO DE PRODUÇÃO DO OPERADOR" in ctx.text
        assert any(source.startswith("REPORT:") for source in ctx.sources)
        print("AT-06B6 SMOKE: OK")
        print("archive=inquerito/cpf/nome assistant_context=ok header_product=ok")
    finally:
        db.close()


if __name__ == "__main__":
    main()
