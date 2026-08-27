"""AT-06B-CURATED-01 G3 smoke: transactional Case document intake."""

from __future__ import annotations

import hashlib
import io
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.operator import AuditLog, Operator  # noqa: F401
from app.models.photo import Photo  # noqa: F401
from app.models.platea import SharedCase, SharedDocument
from app.models.workspace import InvestigativeWorkspace  # noqa: F401
import app.services.document_intake_service as intake_module
from app.services.document_intake_service import (
    InvalidDocumentContent,
    UnsupportedDocumentType,
    incorporate_document,
)
from app.services.storage_service import LocalCaseStorage


PDF_A = b"%PDF-1.7\nCIRCE ATHENA ORIGINAL A\n%%EOF\n"
PDF_LEGACY = b"%PDF-1.7\nCIRCE ATHENA LEGACY\n%%EOF\n"
PDF_FAILURE = b"%PDF-1.7\nCIRCE ATHENA FAILURE\n%%EOF\n"


def make_case(ref: str) -> SharedCase:
    return SharedCase(
        case_ref=ref,
        title=ref,
        status="aberto",
        published_by="smoke",
        published_at=datetime.now(timezone.utc),
        published_version=1,
    )


def physical_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and ".tmp" not in path.parts
    )


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    case_a = make_case("AT06B-CASE-A")
    case_b = make_case("AT06B-CASE-B")
    db.add_all([case_a, case_b])
    db.commit()

    sha_legacy = hashlib.sha256(PDF_LEGACY).hexdigest()

    legacy = SharedDocument(
        shared_case_id=case_a.id,
        document_ref="LEGACY-001",
        filename="legado.pdf",
        file_type="pdf",
        sha256=sha_legacy,
        description="Documento metadata-only anterior ao intake físico.",
        imported_at="2026-08-24",
    )
    db.add(legacy)
    db.commit()
    legacy_id = legacy.id

    with tempfile.TemporaryDirectory(
        prefix="circe-at06b-intake-"
    ) as tmp:
        root = Path(tmp) / "storage"
        storage = LocalCaseStorage(root)

        # 1. novo material físico no Caso A
        created = incorporate_document(
            db,
            storage=storage,
            case_ref=case_a.case_ref,
            source=io.BytesIO(PDF_A),
            original_filename="relatorio_operacao.pdf",
            max_bytes=1024 * 1024,
            operator_id=1,
            operator_username="smoke",
            storage_origin="smoke_case_intake",
        )

        assert created.status == "created"
        assert created.duplicate is False
        assert created.document.filename == "relatorio_operacao.pdf"
        assert created.document.mime_type == "application/pdf"
        assert created.document.physical_available is True

        original_document_id = created.document.id
        original_relpath = created.document.storage_relpath

        assert storage.resolve(original_relpath).read_bytes() == PDF_A
        assert len(physical_files(root)) == 1

        # 2. mesmo conteúdo no mesmo Caso -> nenhuma nova cópia
        duplicate = incorporate_document(
            db,
            storage=storage,
            case_ref=case_a.case_ref,
            source=io.BytesIO(PDF_A),
            original_filename="outra_copia.pdf",
            max_bytes=1024 * 1024,
            operator_username="smoke",
        )

        assert duplicate.status == "duplicate"
        assert duplicate.duplicate is True
        assert duplicate.document.id == original_document_id
        assert len(physical_files(root)) == 1

        # 3. mesmo conteúdo em outro Caso é permitido:
        # deduplicação é case-scoped, não global.
        other_case = incorporate_document(
            db,
            storage=storage,
            case_ref=case_b.case_ref,
            source=io.BytesIO(PDF_A),
            original_filename="mesmo_original.pdf",
            max_bytes=1024 * 1024,
            operator_username="smoke",
        )

        assert other_case.status == "created"
        assert other_case.document.shared_case_id == case_b.id
        assert other_case.document.id != original_document_id
        assert len(physical_files(root)) == 2

        # 4. SHA já conhecido em metadata-only:
        # completar registro, não duplicá-lo.
        hydrated = incorporate_document(
            db,
            storage=storage,
            case_ref=case_a.case_ref,
            source=io.BytesIO(PDF_LEGACY),
            original_filename="legado_original.pdf",
            max_bytes=1024 * 1024,
            operator_username="smoke",
        )

        assert hydrated.status == "hydrated"
        assert hydrated.document.id == legacy_id
        assert hydrated.document.filename == "legado.pdf"
        assert hydrated.document.storage_state == "physical_available"
        assert storage.resolve(
            hydrated.document.storage_relpath
        ).read_bytes() == PDF_LEGACY
        assert len(physical_files(root)) == 3

        # 5. extensão fora da allowlist.
        try:
            incorporate_document(
                db,
                storage=storage,
                case_ref=case_a.case_ref,
                source=io.BytesIO(b"MZ executable"),
                original_filename="arquivo.exe",
                max_bytes=1024,
            )
            raise AssertionError("Extensão proibida foi aceita.")
        except UnsupportedDocumentType:
            pass

        # 6. extensão PDF mas conteúdo não-PDF.
        try:
            incorporate_document(
                db,
                storage=storage,
                case_ref=case_a.case_ref,
                source=io.BytesIO(b"isto nao e pdf"),
                original_filename="falso.pdf",
                max_bytes=1024,
            )
            raise AssertionError("Conteúdo falso foi aceito.")
        except InvalidDocumentContent:
            pass

        assert len(physical_files(root)) == 3

        # 7. Falha depois da gravação física:
        # rollback no banco + compensação do arquivo.
        before_documents = db.query(SharedDocument).count()
        before_files = len(physical_files(root))

        original_log_action = intake_module.log_action

        def explode_audit(*args, **kwargs):
            raise RuntimeError("falha de auditoria simulada")

        intake_module.log_action = explode_audit

        try:
            try:
                incorporate_document(
                    db,
                    storage=storage,
                    case_ref=case_a.case_ref,
                    source=io.BytesIO(PDF_FAILURE),
                    original_filename="falha_controlada.pdf",
                    max_bytes=1024 * 1024,
                    operator_username="smoke",
                )
                raise AssertionError(
                    "Falha transacional simulada não propagou."
                )
            except RuntimeError as exc:
                assert "falha de auditoria simulada" in str(exc)
        finally:
            intake_module.log_action = original_log_action

        assert db.query(SharedDocument).count() == before_documents
        assert len(physical_files(root)) == before_files

        failure_sha = hashlib.sha256(PDF_FAILURE).hexdigest()
        assert (
            db.query(SharedDocument)
            .filter(SharedDocument.sha256 == failure_sha)
            .count()
            == 0
        )

        # 8. Auditoria real existe para operações válidas.
        actions = {
            row.action
            for row in db.query(AuditLog).all()
        }

        assert "document_intake_completed" in actions
        assert "document_intake_duplicate_detected" in actions
        assert "document_physical_original_attached" in actions

        # 9. nenhum Workspace foi necessário.
        assert db.query(InvestigativeWorkspace).count() == 0

    print("AT-06B-CURATED-01 DOCUMENT INTAKE SMOKE: OK")
    print("new-document=created")
    print("same-case-duplicate=blocked")
    print("cross-case-same-hash=allowed")
    print("metadata-only=hydrated")
    print("extension-allowlist=enforced")
    print("content-mismatch=rejected")
    print("audit=same-transaction")
    print("db-failure=physical-compensation")
    print("workspace-required=no")


if __name__ == "__main__":
    main()
