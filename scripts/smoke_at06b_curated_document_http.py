"""AT-06B-CURATED-01 G4 smoke: authenticated HTTP intake and retrieval."""

from __future__ import annotations

import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base
from app.middleware.auth_guard import AuthGuard
from app.models.operator import AuditLog, Operator  # noqa: F401
from app.models.photo import Photo  # noqa: F401
from app.models.platea import SharedCase, SharedDocument
from app.models.workspace import InvestigativeWorkspace  # noqa: F401
import app.routes.documents as document_routes


PDF = b"%PDF-1.7\nCIRCE ATHENA HTTP ORIGINAL\n%%EOF\n"


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="circe-at06b-http-"
    ) as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / "http-smoke.db"
        app_data = tmp_path / "appdata"

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )

        db = Session()

        case = SharedCase(
            case_ref="AT06B-HTTP",
            title="AT06B HTTP Smoke",
            status="aberto",
            published_by="smoke",
            published_at=datetime.now(timezone.utc),
            published_version=1,
        )
        db.add(case)
        db.flush()

        metadata_only = SharedDocument(
            shared_case_id=case.id,
            document_ref="META-ONLY-001",
            filename="somente_metadado.pdf",
            file_type="pdf",
            sha256="e" * 64,
            imported_at="2026-08-24",
        )
        db.add(metadata_only)
        db.commit()

        metadata_only_id = metadata_only.id
        db.close()

        # Route dependencies are redirected only inside this smoke.
        original_session_local = document_routes.SessionLocal
        original_data_dir = document_routes.settings.data_dir
        original_storage_dir = (
            document_routes.settings.case_storage_dir
        )
        original_limit = (
            document_routes.settings.document_intake_max_bytes
        )

        document_routes.SessionLocal = Session
        document_routes.settings.data_dir = str(app_data)
        document_routes.settings.case_storage_dir = "case_storage"
        document_routes.settings.document_intake_max_bytes = 128

        app = FastAPI()
        app.add_middleware(AuthGuard)
        app.add_middleware(
            SessionMiddleware,
            secret_key="at06b-http-smoke-secret",
        )
        app.include_router(document_routes.router)

        @app.post("/login")
        async def login(request: Request):
            request.session["operator"] = {
                "id": 1,
                "username": "smoke",
            }
            return JSONResponse({"ok": True})

        try:
            with TestClient(app) as client:
                # 1. rota protegida sem sessão.
                response = client.post(
                    "/api/cases/AT06B-HTTP/documents/intake",
                    files={
                        "file": (
                            "nao_autorizado.pdf",
                            PDF,
                            "application/pdf",
                        )
                    },
                    follow_redirects=False,
                )
                assert response.status_code == 302
                assert response.headers["location"] == "/login"

                # 2. estabelece sessão autorizada.
                response = client.post("/login")
                assert response.status_code == 200

                # 3. intake real.
                # MIME declarado pelo cliente é propositalmente genérico:
                # o backend deve validar o conteúdo.
                response = client.post(
                    "/api/cases/AT06B-HTTP/documents/intake",
                    files={
                        "file": (
                            "relatorio_http.pdf",
                            PDF,
                            "application/octet-stream",
                        )
                    },
                )

                assert response.status_code == 201
                payload = response.json()

                assert payload["status"] == "created"
                assert payload["duplicate"] is False
                assert (
                    payload["document"]["filename"]
                    == "relatorio_http.pdf"
                )
                assert (
                    payload["document"]["mime_type"]
                    == "application/pdf"
                )
                assert (
                    payload["document"]["storage_state"]
                    == "physical_available"
                )
                assert "storage_relpath" not in payload["document"]

                document_id = payload["document"]["id"]

                # 4. recuperação autorizada do original.
                response = client.get(
                    f"/api/documents/{document_id}/original"
                )

                assert response.status_code == 200
                assert response.content == PDF
                assert (
                    response.headers["content-type"]
                    .startswith("application/pdf")
                )
                assert "attachment" in response.headers[
                    "content-disposition"
                ].lower()

                # 5. duplicidade no mesmo Caso.
                response = client.post(
                    "/api/cases/AT06B-HTTP/documents/intake",
                    files={
                        "file": (
                            "segunda_copia.pdf",
                            PDF,
                            "application/pdf",
                        )
                    },
                )

                assert response.status_code == 200
                duplicate = response.json()

                assert duplicate["status"] == "duplicate"
                assert duplicate["duplicate"] is True
                assert duplicate["document"]["id"] == document_id

                # 6. extensão proibida.
                response = client.post(
                    "/api/cases/AT06B-HTTP/documents/intake",
                    files={
                        "file": (
                            "arquivo.exe",
                            b"MZ fake executable",
                            "application/octet-stream",
                        )
                    },
                )
                assert response.status_code == 415

                # 7. extensão permitida, conteúdo falso.
                response = client.post(
                    "/api/cases/AT06B-HTTP/documents/intake",
                    files={
                        "file": (
                            "falso.pdf",
                            b"isto nao e pdf",
                            "application/pdf",
                        )
                    },
                )
                assert response.status_code == 422

                # 8. arquivo acima do limite configurado no smoke.
                oversized = b"%PDF-" + (b"x" * 200)

                response = client.post(
                    "/api/cases/AT06B-HTTP/documents/intake",
                    files={
                        "file": (
                            "grande.pdf",
                            oversized,
                            "application/pdf",
                        )
                    },
                )
                assert response.status_code == 413

                # 9. Caso inexistente.
                response = client.post(
                    "/api/cases/NAO-EXISTE/documents/intake",
                    files={
                        "file": (
                            "arquivo.pdf",
                            PDF,
                            "application/pdf",
                        )
                    },
                )
                assert response.status_code == 404

                # 10. metadata-only continua explicitamente distinto.
                response = client.get(
                    f"/api/documents/{metadata_only_id}/original"
                )
                assert response.status_code == 409

            verify = Session()

            documents = verify.query(SharedDocument).all()
            physical = [
                item
                for item in documents
                if item.storage_relpath
            ]

            # Somente um original físico: duplicidade não criou outro.
            assert len(physical) == 1
            assert physical[0].id == document_id
            assert physical[0].sha256 == hashlib.sha256(PDF).hexdigest()

            storage_root = app_data / "case_storage"
            physical_files = [
                path
                for path in storage_root.rglob("*")
                if path.is_file() and ".tmp" not in path.parts
            ]
            assert len(physical_files) == 1
            assert physical_files[0].read_bytes() == PDF

            actions = [
                row.action
                for row in verify.query(AuditLog).all()
            ]

            assert "document_intake_completed" in actions
            assert "document_intake_duplicate_detected" in actions
            assert "document_original_retrieved" in actions
            assert "document_intake_failed" in actions
            assert "document_original_retrieval_failed" in actions

            assert verify.query(InvestigativeWorkspace).count() == 0
            verify.close()

        finally:
            document_routes.SessionLocal = original_session_local
            document_routes.settings.data_dir = original_data_dir
            document_routes.settings.case_storage_dir = (
                original_storage_dir
            )
            document_routes.settings.document_intake_max_bytes = (
                original_limit
            )
            engine.dispose()

    print("AT-06B-CURATED-01 DOCUMENT HTTP SMOKE: OK")
    print("unauthenticated-request=blocked")
    print("authenticated-intake=created")
    print("client-mime=not-trusted")
    print("original-retrieval=byte-identical")
    print("storage-path=not-exposed")
    print("duplicate=no-second-copy")
    print("unsupported-extension=415")
    print("content-mismatch=422")
    print("oversized=413")
    print("unknown-case=404")
    print("metadata-only=409")
    print("failure-audit=present")
    print("retrieval-audit=present")
    print("workspace-required=no")


if __name__ == "__main__":
    main()
