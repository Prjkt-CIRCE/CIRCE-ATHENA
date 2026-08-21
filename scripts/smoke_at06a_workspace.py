"""AT-06A smoke test — Workspace core sem tocar no banco operacional."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.operator import Operator  # noqa: F401
from app.models.platea import SharedCase, SharedDocument, SharedPerson  # noqa: F401
from app.models.workspace import InvestigativeWorkspace  # noqa: F401
from app.services.workspace_service import (
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
        source_tokens=[f"person:{person.id}", f"document:{document.id}"],
        operator_id=1,
        operator_username="smoke",
    )
    assert error is None and block is not None
    db.commit()

    context = build_block_context(db, case_ref=case.case_ref, block_id=block.id)
    assert context is not None
    assert "Pessoa Teste" in context.text
    assert "documento_teste.pdf" in context.text
    assert "BLOCO:" in context.sources[0]

    # AT06A_UNDO_V1
    source_to_remove = block.sources[1]
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

    print("AT-06A SMOKE: OK")
    print(f"workspace={workspace.id} block={block.id} undo=ok")


if __name__ == "__main__":
    main()
