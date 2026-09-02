"""UX-03A domain/persistence smoke using synthetic data and a temporary database."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


_TEMP_DATA = tempfile.TemporaryDirectory(prefix="circe-ux03a-domain-data-")
os.environ["DATA_DIR"] = _TEMP_DATA.name

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.operator import AuditLog  # noqa: F401
from app.models.platea import SharedCase, SharedDocument
from app.models.workspace import InvestigativeBlock, InvestigativeBlockSource, InvestigativeWorkspace
from app.models.workspace_product import ProductSectionBlock, WorkspaceProduct  # noqa: F401
from app.services.workspace_product_service import (
    ProductServiceError,
    RevisionConflict,
    create_product,
    get_product,
    reorder_sections,
    set_section_blocks,
    update_section,
)
from app.services.workspace_service import discard_block


def main() -> None:
    db_path = Path(_TEMP_DATA.name) / "domain-smoke.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime.now(timezone.utc)
    cases = [
        SharedCase(case_ref="UX03A-A", title="Caso A", status="aberto", published_by="smoke", published_at=now, published_version=1),
        SharedCase(case_ref="UX03A-B", title="Caso B", status="aberto", published_by="smoke", published_at=now, published_version=1),
    ]
    db.add_all(cases)
    db.flush()
    workspaces = [
        InvestigativeWorkspace(shared_case_id=item.id, created_by_operator_id=1, created_by_username="smoke", created_at=now, updated_at=now)
        for item in cases
    ]
    db.add_all(workspaces)
    db.flush()
    document = SharedDocument(
        shared_case_id=cases[0].id, document_ref="DOC-SYNTH", filename="sintetico.txt",
        file_type="txt", sha256="a" * 64, description="fixture metadata-only", imported_at="2026-09-02",
    )
    block_a = InvestigativeBlock(
        workspace_id=workspaces[0].id, title="Bloco sintético", summary="Resumo",
        status="working", created_by_operator_id=1, created_by_username="smoke",
        authorship_mode="literal", created_at=now, updated_at=now,
    )
    block_b = InvestigativeBlock(
        workspace_id=workspaces[1].id, title="Bloco externo", summary=None,
        status="working", created_by_operator_id=1, created_by_username="smoke",
        authorship_mode="literal", created_at=now, updated_at=now,
    )
    db.add_all([document, block_a, block_b])
    db.flush()
    db.add(InvestigativeBlockSource(
        block_id=block_a.id, source_type="document", source_key="ref:DOC-SYNTH",
        source_label_snapshot=document.filename, source_snapshot="{}", relation="context",
        position=0, added_at=now,
    ))
    db.commit()

    product = create_product(
        db, workspace_id=workspaces[0].id, title="  Produto Alfa  ",
        section_titles=["Introdução", "Conclusão"], operator_id=1, operator_username="smoke",
    )
    db.commit()
    assert product.revision == 1
    assert [item.position for item in product.sections] == [0, 1]
    section_a, section_b = product.sections
    stable_ids = [section_a.id, section_b.id]

    product = update_section(
        db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_a.id,
        expected_revision=1, title="Síntese", body="Linha um\nLinha dois — ação",
        update_title=True, update_body=True, operator_id=1, operator_username="smoke",
    )
    db.commit()
    assert product.revision == 2

    product = set_section_blocks(
        db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_a.id,
        block_ids=[block_a.id], expected_revision=2, operator_id=1, operator_username="smoke",
    )
    db.commit()
    product = set_section_blocks(
        db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_b.id,
        block_ids=[block_a.id], expected_revision=3, operator_id=1, operator_username="smoke",
    )
    db.commit()

    second = create_product(
        db, workspace_id=workspaces[0].id, title="Produto Beta", section_titles=["Única"],
        operator_id=1, operator_username="smoke",
    )
    db.commit()
    second = set_section_blocks(
        db, workspace_id=workspaces[0].id, product_id=second.id, section_id=second.sections[0].id,
        block_ids=[block_a.id], expected_revision=1, operator_id=1, operator_username="smoke",
    )
    db.commit()
    assert db.query(ProductSectionBlock).filter_by(block_id=block_a.id).count() == 3
    assert db.query(InvestigativeBlockSource).filter_by(block_id=block_a.id).count() == 1

    product = reorder_sections(
        db, workspace_id=workspaces[0].id, product_id=product.id,
        section_ids=[section_b.id, section_a.id], expected_revision=4,
        operator_id=1, operator_username="smoke",
    )
    db.commit()
    ordered = get_product(db, workspaces[0].id, product.id)
    assert [item["id"] for item in ordered["sections"]] == [section_b.id, section_a.id]
    assert ordered["sections"][1]["body"] == "Linha um\nLinha dois — ação"
    assert ordered["sections"][1]["blocks"][0]["block_id"] == block_a.id

    product = set_section_blocks(
        db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_a.id,
        block_ids=[], expected_revision=5, operator_id=1, operator_username="smoke",
    )
    db.commit()
    assert len(get_product(db, workspaces[0].id, product.id)["sections"][0]["blocks"]) == 1
    assert len(get_product(db, workspaces[0].id, product.id)["sections"][1]["blocks"]) == 0

    discarded, discard_error = discard_block(
        db,
        workspace_id=workspaces[0].id,
        block_id=block_a.id,
    )
    assert discard_error is None and discarded is not None
    db.commit()
    persisted = get_product(db, workspaces[0].id, product.id)
    assert persisted["sections"][0]["blocks"][0]["availability"] == "discarded"

    # An existing discarded reference can be retained in place.
    product = set_section_blocks(
        db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_b.id,
        block_ids=[block_a.id], expected_revision=6, operator_id=1, operator_username="smoke",
    )
    db.commit()
    retained = get_product(db, workspaces[0].id, product.id)
    assert retained["revision"] == 7
    assert retained["sections"][0]["blocks"][0]["availability"] == "discarded"

    # It can also be removed without changing or reviving the original block.
    product = set_section_blocks(
        db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_b.id,
        block_ids=[], expected_revision=7, operator_id=1, operator_username="smoke",
    )
    db.commit()
    assert get_product(db, workspaces[0].id, product.id)["sections"][0]["blocks"] == []
    assert db.query(InvestigativeBlock).filter_by(id=block_a.id).one().status == "discarded"

    # Once removed, the discarded block cannot be associated anew.
    try:
        set_section_blocks(
            db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_a.id,
            block_ids=[block_a.id], expected_revision=8, operator_id=1, operator_username="smoke",
        )
        raise AssertionError("discarded block was associated anew")
    except ProductServiceError:
        db.rollback()

    before = get_product(db, workspaces[0].id, product.id)
    try:
        set_section_blocks(
            db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_a.id,
            block_ids=[block_b.id], expected_revision=8, operator_id=1, operator_username="smoke",
        )
        raise AssertionError("cross-workspace block was accepted")
    except ProductServiceError:
        db.rollback()
    assert get_product(db, workspaces[0].id, product.id) == before

    winner = update_section(
        db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_a.id,
        expected_revision=8, title=None, body="Vencedor", update_title=False, update_body=True,
        operator_id=1, operator_username="smoke",
    )
    db.commit()
    assert winner.revision == 9
    try:
        update_section(
            db, workspace_id=workspaces[0].id, product_id=product.id, section_id=section_a.id,
            expected_revision=8, title=None, body="Obsoleto", update_title=False, update_body=True,
            operator_id=1, operator_username="smoke",
        )
        raise AssertionError("stale revision was accepted")
    except RevisionConflict as error:
        db.rollback()
        assert error.current_revision == 9

    workspace_id = workspaces[0].id
    product_id = product.id
    section_a_id = section_a.id
    section_b_id = section_b.id
    db.close()
    reopened = Session()
    restored = get_product(reopened, workspace_id, product_id)
    assert restored["revision"] == 9
    target = next(item for item in restored["sections"] if item["id"] == section_a_id)
    assert target["title"] == "Síntese" and target["body"] == "Vencedor"
    assert [item["id"] for item in restored["sections"]] == [section_b_id, section_a_id] == stable_ids[::-1]
    reopened.close()
    engine.dispose()
    _TEMP_DATA.cleanup()

    print("UX-03A PRODUCT/SECTIONS SMOKE: OK")
    print("persistence=reopened; unicode=preserved; reuse=reference-only")
    print("reorder=stable; discarded=signaled; isolation=preserved; conflict=rejected")


if __name__ == "__main__":
    main()
