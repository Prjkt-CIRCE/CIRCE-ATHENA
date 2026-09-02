"""UX-03A HTTP/auth/audit smoke using synthetic data and a temporary database."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


_TEMP_DATA = tempfile.TemporaryDirectory(prefix="circe-ux03a-http-data-")
os.environ["DATA_DIR"] = _TEMP_DATA.name

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as OrmSession, sessionmaker
from sqlalchemy.pool import NullPool
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base
from app.middleware.auth_guard import AuthGuard
from app.models.operator import AuditLog
from app.models.platea import SharedCase, SharedDocument
from app.models.workspace import InvestigativeBlock, InvestigativeBlockSource, InvestigativeWorkspace
from app.models.workspace_product import WorkspaceProduct  # noqa: F401
from app.models.workspace_product import ProductSection, ProductSectionBlock
import app.routes.workspace_products as product_routes


def main() -> None:
    db_path = Path(_TEMP_DATA.name) / "http-smoke.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, poolclass=NullPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    now = datetime.now(timezone.utc)
    cases = [
        SharedCase(case_ref="HTTP-A", title="Caso HTTP A", status="aberto", published_by="smoke", published_at=now, published_version=1),
        SharedCase(case_ref="HTTP-B", title="Caso HTTP B", status="aberto", published_by="smoke", published_at=now, published_version=1),
    ]
    db.add_all(cases)
    db.flush()
    workspaces = [
        InvestigativeWorkspace(shared_case_id=item.id, created_by_operator_id=7, created_by_username="http-smoke", created_at=now, updated_at=now)
        for item in cases
    ]
    db.add_all(workspaces)
    db.flush()
    document = SharedDocument(
        shared_case_id=cases[0].id, document_ref="HTTP-DOC", filename="http-synthetic.txt",
        file_type="txt", sha256="c" * 64, description="synthetic", imported_at="2026-09-02",
    )
    blocks = [
        InvestigativeBlock(
            workspace_id=workspace.id, title=f"Bloco HTTP {index}", summary=None,
            status="working", created_by_operator_id=7, created_by_username="http-smoke",
            authorship_mode="literal", created_at=now, updated_at=now,
        )
        for index, workspace in enumerate(workspaces, start=1)
    ]
    db.add_all([document, *blocks])
    db.flush()
    db.add(InvestigativeBlockSource(
        block_id=blocks[0].id, source_type="document", source_key="ref:HTTP-DOC",
        source_label_snapshot=document.filename, source_snapshot="{}", relation="context",
        position=0, added_at=now,
    ))
    db.commit()
    workspace_ids = [item.id for item in workspaces]
    block_ids = [item.id for item in blocks]
    db.close()

    original_session_local = product_routes.SessionLocal
    original_log_action = product_routes.log_action
    product_routes.SessionLocal = Session
    app = FastAPI()
    app.add_middleware(AuthGuard)
    app.add_middleware(SessionMiddleware, secret_key="ux03a-http-smoke-secret")
    app.include_router(product_routes.router)

    @app.post("/login")
    async def login(request: Request):
        request.session["operator"] = {"id": 7, "username": "http-smoke"}
        return JSONResponse({"ok": True})

    try:
        with TestClient(app) as client:
            response = client.get(f"/api/workspaces/{workspace_ids[0]}/products", follow_redirects=False)
            assert response.status_code == 302 and response.headers["location"] == "/login"
            assert client.post("/login").status_code == 200

            response = client.get(f"/api/workspaces/{workspace_ids[0]}/products")
            assert response.status_code == 200 and response.json() == {"products": []}
            verify = Session()
            assert verify.query(WorkspaceProduct).count() == 0
            verify.close()

            response = client.post(
                f"/api/workspaces/{workspace_ids[0]}/products",
                json={"title": "Produto HTTP", "section_titles": ["Primeira", "Segunda"]},
            )
            assert response.status_code == 201
            product = response.json()
            product_id = product["id"]
            first_id, second_id = [item["id"] for item in product["sections"]]
            assert product["revision"] == 1

            response = client.patch(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}",
                json={"body": "Texto HTTP\ncom Unicode: seção", "expected_revision": 1},
            )
            assert response.status_code == 200 and response.json()["revision"] == 2

            response = client.post(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections",
                json={"title": "Terceira", "expected_revision": 2},
            )
            assert response.status_code == 201 and response.json()["revision"] == 3
            third_id = response.json()["sections"][2]["id"]

            response = client.put(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/order",
                json={"section_ids": [third_id, second_id, first_id], "expected_revision": 3},
            )
            assert response.status_code == 200 and response.json()["revision"] == 4
            assert [item["id"] for item in response.json()["sections"]] == [third_id, second_id, first_id]

            response = client.put(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}/blocks",
                json={"block_ids": [block_ids[0]], "expected_revision": 4},
            )
            assert response.status_code == 200 and response.json()["revision"] == 5
            assert response.json()["sections"][2]["blocks"][0]["block_id"] == block_ids[0]

            stale = client.patch(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}",
                json={"body": "Não sobrescrever", "expected_revision": 1},
            )
            assert stale.status_code == 409
            assert stale.json()["code"] == "revision_conflict" and stale.json()["current_revision"] == 5

            cross = client.put(
                f"/api/workspaces/{workspace_ids[1]}/products/{product_id}/sections/order",
                json={"section_ids": [third_id, second_id, first_id], "expected_revision": 5},
            )
            assert cross.status_code == 404 and cross.json()["code"] == "not_found"

            cross_block = client.put(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}/blocks",
                json={"block_ids": [block_ids[1]], "expected_revision": 5},
            )
            assert cross_block.status_code == 422 and cross_block.json()["code"] == "validation_error"

            invalid_payloads = [
                {"title": "", "section_titles": []},
                {"title": "Válido", "section_titles": [], "unknown": True},
                {"title": "x" * 257, "section_titles": []},
            ]
            for payload in invalid_payloads:
                response = client.post(f"/api/workspaces/{workspace_ids[0]}/products", json=payload)
                assert response.status_code == 422
            response = client.patch(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}",
                json={"expected_revision": 5},
            )
            assert response.status_code == 422
            response = client.patch(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}",
                json={"body": "x" * 50_001, "expected_revision": 5},
            )
            assert response.status_code == 422

            def failing_audit(*args, **kwargs):
                raise RuntimeError("synthetic audit failure")

            product_routes.log_action = failing_audit
            failed = client.patch(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}",
                json={"body": "Não deve persistir", "expected_revision": 5},
            )
            assert failed.status_code == 500 and failed.json()["code"] == "internal_error"
            product_routes.log_action = original_log_action

            response = client.get(f"/api/workspaces/{workspace_ids[0]}/products/{product_id}")
            assert response.status_code == 200
            after = response.json()
            assert after["revision"] == 5
            persisted_first = next(item for item in after["sections"] if item["id"] == first_id)
            assert persisted_first["body"] == "Texto HTTP\ncom Unicode: seção"

            # Regression: stale revision takes precedence over a permutation
            # that became incomplete because another operation added a Section.
            response = client.post(
                f"/api/workspaces/{workspace_ids[0]}/products",
                json={"title": "Produto concorrente", "section_titles": ["Antiga A", "Antiga B"]},
            )
            assert response.status_code == 201
            concurrent = response.json()
            concurrent_id = concurrent["id"]
            old_section_ids = [item["id"] for item in concurrent["sections"]]
            response = client.post(
                f"/api/workspaces/{workspace_ids[0]}/products/{concurrent_id}/sections",
                json={"title": "Nova concorrente", "expected_revision": 1},
            )
            assert response.status_code == 201 and response.json()["revision"] == 2
            state_before_stale_reorder = response.json()

            verify_before = Session()
            successful_reorders_before = verify_before.query(AuditLog).filter_by(
                action="product_sections_reordered"
            ).count()
            verify_before.close()

            response = client.put(
                f"/api/workspaces/{workspace_ids[0]}/products/{concurrent_id}/sections/order",
                json={"section_ids": old_section_ids, "expected_revision": 1},
            )
            assert response.status_code == 409
            assert response.json()["code"] == "revision_conflict"
            assert response.json()["current_revision"] == 2

            response = client.get(
                f"/api/workspaces/{workspace_ids[0]}/products/{concurrent_id}"
            )
            assert response.status_code == 200 and response.json() == state_before_stale_reorder
            verify_after = Session()
            assert verify_after.query(AuditLog).filter_by(
                action="product_sections_reordered"
            ).count() == successful_reorders_before
            verify_after.close()

            # With the current revision, the same incomplete permutation is 422.
            response = client.put(
                f"/api/workspaces/{workspace_ids[0]}/products/{concurrent_id}/sections/order",
                json={"section_ids": old_section_ids, "expected_revision": 2},
            )
            assert response.status_code == 422 and response.json()["code"] == "validation_error"

            # Commit failure after both mutation and audit have been flushed.
            snapshot_db = Session()
            before_commit_failure = {
                "products": snapshot_db.query(WorkspaceProduct.id, WorkspaceProduct.revision, WorkspaceProduct.title).order_by(WorkspaceProduct.id).all(),
                "sections": snapshot_db.query(ProductSection.id, ProductSection.product_id, ProductSection.title, ProductSection.body, ProductSection.position).order_by(ProductSection.id).all(),
                "links": snapshot_db.query(ProductSectionBlock.id, ProductSectionBlock.section_id, ProductSectionBlock.block_id, ProductSectionBlock.position).order_by(ProductSectionBlock.id).all(),
                "audit": snapshot_db.query(AuditLog.id, AuditLog.action, AuditLog.current_hash).order_by(AuditLog.id).all(),
            }
            snapshot_db.close()

            class FlushThenFailCommitSession(OrmSession):
                def commit(self) -> None:
                    self.flush()
                    raise RuntimeError("synthetic commit failure after flush")

            FailingSession = sessionmaker(
                autocommit=False, autoflush=False, bind=engine, class_=FlushThenFailCommitSession,
            )
            product_routes.SessionLocal = FailingSession
            failed_commit = client.patch(
                f"/api/workspaces/{workspace_ids[0]}/products/{product_id}/sections/{first_id}",
                json={"title": "Não confirmar", "body": "Rollback completo", "expected_revision": 5},
            )
            assert failed_commit.status_code == 500
            assert failed_commit.json()["code"] == "internal_error"
            product_routes.SessionLocal = Session

            after_db = Session()
            after_commit_failure = {
                "products": after_db.query(WorkspaceProduct.id, WorkspaceProduct.revision, WorkspaceProduct.title).order_by(WorkspaceProduct.id).all(),
                "sections": after_db.query(ProductSection.id, ProductSection.product_id, ProductSection.title, ProductSection.body, ProductSection.position).order_by(ProductSection.id).all(),
                "links": after_db.query(ProductSectionBlock.id, ProductSectionBlock.section_id, ProductSectionBlock.block_id, ProductSectionBlock.position).order_by(ProductSectionBlock.id).all(),
                "audit": after_db.query(AuditLog.id, AuditLog.action, AuditLog.current_hash).order_by(AuditLog.id).all(),
            }
            after_db.close()
            assert after_commit_failure == before_commit_failure

        verify = Session()
        assert verify.query(WorkspaceProduct).count() == 2
        actions = [item.action for item in verify.query(AuditLog).order_by(AuditLog.id).all()]
        assert actions == [
            "workspace_product_created",
            "product_section_updated",
            "product_section_created",
            "product_sections_reordered",
            "product_section_blocks_updated",
            "workspace_product_created",
            "product_section_created",
        ]
        verify.close()
    finally:
        product_routes.SessionLocal = original_session_local
        product_routes.log_action = original_log_action
        engine.dispose()
        _TEMP_DATA.cleanup()

    print("UX-03A PRODUCT HTTP SMOKE: OK")
    print("auth=302; empty-get=no-write; validation=422; isolation=404")
    print("conflict=409; audit=same-transaction; audit-failure=rollback")
    print("stale-reorder=409-before-state-validation; current-invalid-reorder=422")
    print("commit-failure-after-flush=full-rollback")


if __name__ == "__main__":
    main()
