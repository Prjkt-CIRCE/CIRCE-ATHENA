"""AT-06B-CURATED-01 G2 smoke: SharedDocument physical/metadata-only contract."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.operator import Operator  # noqa: F401
from app.models.photo import Photo  # noqa: F401
from app.models.platea import SharedCase, SharedDocument
from app.models.workspace import InvestigativeWorkspace  # noqa: F401


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    case = SharedCase(
        case_ref="AT06B-G2",
        title="G2 Model Smoke",
        status="aberto",
        published_by="smoke",
        published_at=datetime.now(timezone.utc),
        published_version=1,
    )
    db.add(case)
    db.flush()

    legacy = SharedDocument(
        shared_case_id=case.id,
        document_ref="LEGACY-001",
        filename="documento_legado.pdf",
        file_type="pdf",
        sha256="a" * 64,
        description="Registro anterior ao storage físico.",
        imported_at="2026-08-24",
    )

    physical = SharedDocument(
        shared_case_id=case.id,
        document_ref="PHYSICAL-001",
        filename="original.pdf",
        file_type="pdf",
        sha256="b" * 64,
        storage_relpath="cases/1/documents/0123456789abcdef",
        mime_type="application/pdf",
        size_bytes=1234,
        storage_origin="case_intake",
        stored_at=datetime.now(timezone.utc),
    )

    db.add_all([legacy, physical])
    db.commit()

    db.refresh(legacy)
    db.refresh(physical)

    assert legacy.storage_relpath is None
    assert legacy.mime_type is None
    assert legacy.size_bytes is None
    assert legacy.storage_origin is None
    assert legacy.stored_at is None
    assert legacy.storage_state == "metadata_only"
    assert legacy.physical_available is False

    assert physical.storage_relpath == "cases/1/documents/0123456789abcdef"
    assert physical.mime_type == "application/pdf"
    assert physical.size_bytes == 1234
    assert physical.storage_origin == "case_intake"
    assert physical.stored_at is not None
    assert physical.storage_state == "physical_available"
    assert physical.physical_available is True

    print("AT-06B-CURATED-01 DOCUMENT MODEL SMOKE: OK")
    print("legacy-document=metadata_only")
    print("physical-document=physical_available")
    print("legacy-nullability=preserved")
    print("workspace-required=no")


if __name__ == "__main__":
    main()
