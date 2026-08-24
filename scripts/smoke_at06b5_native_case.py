from __future__ import annotations

import asyncio
import io
import shutil
import uuid
from pathlib import Path

from starlette.datastructures import UploadFile

from app.database import SessionLocal
from app.services.case_intake_service import cleanup_stored_paths, create_native_case, ingest_case_uploads
from app.services.workspace_service import open_workspace


def main() -> None:
    db = SessionLocal()
    created_paths: list[str] = []
    try:
        token = uuid.uuid4().hex[:8]
        case = create_native_case(
            db,
            title=f"Smoke caso nativo {token}",
            classification="teste",
            notes="smoke",
            source_unit="TESTE",
            operator_id=None,
            operator_username="smoke",
        )
        assert case.origin_type == "native"
        assert case.case_uuid
        assert case.case_ref.startswith("ATH-")

        upload = UploadFile(filename="ordem_servico_teste.pdf", file=io.BytesIO(b"conteudo de teste AT-06B5"))
        docs, created_paths, duplicates = asyncio.run(
            ingest_case_uploads(
                db,
                case=case,
                uploads=[upload],
                operator_username="smoke",
                intake_bin="inbox",
            )
        )
        assert duplicates == 0
        assert len(docs) == 1
        assert docs[0].sha256
        assert docs[0].storage_path
        assert docs[0].intake_bin == "inbox"
        assert docs[0].origin == "native_intake"

        workspace, created = open_workspace(
            db,
            case_ref=case.case_ref,
            operator_id=None,
            operator_username="smoke",
        )
        assert workspace is not None and created
        print("AT-06B5 SMOKE: OK")
        print(f"case={case.case_ref} intake=1 workspace={workspace.id}")
    finally:
        db.rollback()
        cleanup_stored_paths(created_paths)
        db.close()


if __name__ == "__main__":
    main()
