"""CURATED-01A smoke: canonical, case-scoped material access."""

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.operator import Operator  # noqa: F401
from app.models.photo import Photo  # noqa: F401
from app.models.platea import (
    SharedCase,
    SharedCaseAnnotation,
    SharedDocument,
    SharedLink,
    SharedPerson,
)
from app.models.workspace import InvestigativeWorkspace  # noqa: F401
from app.services.case_material_service import load_case_materials


def make_case(ref: str, title: str) -> SharedCase:
    return SharedCase(
        case_ref=ref,
        title=title,
        status="aberto",
        published_by="smoke",
        published_at=datetime.now(timezone.utc),
        published_version=1,
    )


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    case_a = make_case("CURATED-01-A", "Caso A")
    case_b = make_case("CURATED-01-B", "Caso B")
    case_empty = make_case("CURATED-01-EMPTY", "Caso vazio")
    db.add_all([case_a, case_b, case_empty])
    db.flush()

    db.add_all(
        [
            SharedPerson(
                shared_case_id=case_a.id,
                person_ref="P-002",
                full_name="Pessoa Dois",
            ),
            SharedPerson(
                shared_case_id=case_a.id,
                person_ref="P-001",
                full_name="Pessoa Um",
            ),
            SharedDocument(
                shared_case_id=case_a.id,
                document_ref="D-002",
                filename="dois.pdf",
                sha256="2" * 64,
            ),
            SharedDocument(
                shared_case_id=case_a.id,
                document_ref="D-001",
                filename="um.pdf",
                sha256="1" * 64,
            ),
            SharedLink(
                shared_case_id=case_a.id,
                link_type="relacao",
                entity_a_ref="P-001",
                entity_a_name="Pessoa Um",
                entity_b_ref="P-002",
                entity_b_name="Pessoa Dois",
            ),
            SharedCaseAnnotation(
                shared_case_id=case_a.id,
                content="Anotacao humana do caso A.",
                created_by_operator_id=1,
                created_by_username="smoke",
                created_at=datetime.now(timezone.utc),
                source="human",
            ),
            SharedDocument(
                shared_case_id=case_b.id,
                document_ref="D-FOREIGN",
                filename="outro_caso.pdf",
                sha256="f" * 64,
            ),
        ]
    )
    db.commit()

    assert db.query(InvestigativeWorkspace).count() == 0

    before = {
        "cases": db.query(SharedCase).count(),
        "persons": db.query(SharedPerson).count(),
        "documents": db.query(SharedDocument).count(),
        "links": db.query(SharedLink).count(),
        "annotations": db.query(SharedCaseAnnotation).count(),
        "workspaces": db.query(InvestigativeWorkspace).count(),
    }

    materials = load_case_materials(db, case_ref=case_a.case_ref)
    assert materials is not None
    assert materials.case.id == case_a.id
    assert materials.total_count == 6

    assert [item.id for item in materials.persons] == sorted(
        item.id for item in materials.persons
    )
    assert [item.id for item in materials.documents] == sorted(
        item.id for item in materials.documents
    )

    assert {item.full_name for item in materials.persons} == {
        "Pessoa Um",
        "Pessoa Dois",
    }
    assert {item.filename for item in materials.documents} == {
        "um.pdf",
        "dois.pdf",
    }
    assert all(item.shared_case_id == case_a.id for item in materials.persons)
    assert all(item.shared_case_id == case_a.id for item in materials.documents)
    assert all(item.shared_case_id == case_a.id for item in materials.links)
    assert all(item.shared_case_id == case_a.id for item in materials.annotations)
    assert "outro_caso.pdf" not in {
        item.filename for item in materials.documents
    }

    empty = load_case_materials(db, case_ref=case_empty.case_ref)
    assert empty is not None
    assert empty.total_count == 0
    assert empty.persons == ()
    assert empty.documents == ()
    assert empty.links == ()
    assert empty.annotations == ()

    assert load_case_materials(db, case_ref="NAO-EXISTE") is None

    after = {
        "cases": db.query(SharedCase).count(),
        "persons": db.query(SharedPerson).count(),
        "documents": db.query(SharedDocument).count(),
        "links": db.query(SharedLink).count(),
        "annotations": db.query(SharedCaseAnnotation).count(),
        "workspaces": db.query(InvestigativeWorkspace).count(),
    }

    assert after == before
    assert not db.new
    assert not db.dirty
    assert not db.deleted

    print("CURATED-01A CASE MATERIALS SMOKE: OK")
    print("case-scope=isolated")
    print("workspace-required=no")
    print("manual-selection-required=no")
    print("empty-case=supported")
    print("unknown-case=none")
    print("read-only=yes")
    print("ordering=deterministic")


if __name__ == "__main__":
    main()
