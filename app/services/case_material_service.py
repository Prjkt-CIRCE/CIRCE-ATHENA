from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, selectinload

from app.models.platea import (
    SharedCase,
    SharedCaseAnnotation,
    SharedDocument,
    SharedLink,
    SharedPerson,
)


@dataclass(frozen=True)
class CaseMaterials:
    """Canonical, read-only view of everything that currently belongs to a case."""

    case: SharedCase
    persons: tuple[SharedPerson, ...]
    documents: tuple[SharedDocument, ...]
    links: tuple[SharedLink, ...]
    annotations: tuple[SharedCaseAnnotation, ...]

    @property
    def total_count(self) -> int:
        return (
            len(self.persons)
            + len(self.documents)
            + len(self.links)
            + len(self.annotations)
        )


def load_case_materials(
    db: Session,
    *,
    case_ref: str,
) -> CaseMaterials | None:
    """Return the canonical case material set without requiring a Workspace."""

    case = (
        db.query(SharedCase)
        .options(
            selectinload(SharedCase.persons),
            selectinload(SharedCase.documents),
            selectinload(SharedCase.links),
            selectinload(SharedCase.annotations),
        )
        .filter(SharedCase.case_ref == case_ref)
        .first()
    )
    if not case:
        return None

    return CaseMaterials(
        case=case,
        persons=tuple(sorted(case.persons, key=lambda item: item.id)),
        documents=tuple(sorted(case.documents, key=lambda item: item.id)),
        links=tuple(sorted(case.links, key=lambda item: item.id)),
        annotations=tuple(sorted(case.annotations, key=lambda item: item.id)),
    )
