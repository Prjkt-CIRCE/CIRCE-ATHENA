"""
AT-05.2 — Escrita autorizada pelo usuário.

Primeira ação suportada:
    Anote no caso <REFERENCIA>: <texto>

A ação é preparada, exige confirmação explícita e só então grava uma
anotação separada do dado sincronizado de origem.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.platea import SharedCase, SharedCaseAnnotation


ANNOTATION_COMMAND_RE = re.compile(
    r"""^\s*
    (?:
        anote
        |registre(?:\s+uma)?\s+anota[cç][aã]o
        |adicione(?:\s+uma)?\s+(?:nota|anota[cç][aã]o)
        |inclua(?:\s+uma)?\s+(?:nota|anota[cç][aã]o)
        |acrescente(?:\s+uma)?\s+(?:nota|anota[cç][aã]o)
    )
    \s+(?:no|ao|para\s+o)\s+caso
    \s+([A-Za-z0-9][A-Za-z0-9._/-]{2,})
    \s*:\s*
    (.+?)
    \s*$""",
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

MAX_ANNOTATION_LENGTH = 4000


@dataclass
class AnnotationCommand:
    case_ref: str
    content: str


def parse_annotation_command(question: str) -> AnnotationCommand | None:
    match = ANNOTATION_COMMAND_RE.match(question or "")
    if not match:
        return None

    case_ref = match.group(1).strip(".,;:!?")
    content = match.group(2).strip()

    if not content:
        return None

    return AnnotationCommand(
        case_ref=case_ref,
        content=content[:MAX_ANNOTATION_LENGTH],
    )


def build_pending_annotation(
    db: Session,
    command: AnnotationCommand,
    authorship_mode: str = "literal",
) -> tuple[dict | None, str | None]:
    case = (
        db.query(SharedCase)
        .filter(SharedCase.case_ref == command.case_ref)
        .first()
    )

    if not case:
        return None, f"O caso {command.case_ref} não foi encontrado na base investigativa local."

    action = {
        "action_id": secrets.token_urlsafe(18),
        "type": "add_case_annotation",
        "case_ref": case.case_ref,
        "case_title": case.title,
        "content": command.content,
        "authorship_mode": authorship_mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return action, None


def create_case_annotation(
    db: Session,
    *,
    case_ref: str,
    content: str,
    operator_id: int | None,
    operator_username: str | None,
    authorship_mode: str = "literal",
) -> SharedCaseAnnotation | None:
    case = (
        db.query(SharedCase)
        .filter(SharedCase.case_ref == case_ref)
        .first()
    )
    if not case:
        return None

    annotation = SharedCaseAnnotation(
        shared_case_id=case.id,
        content=content,
        created_by_operator_id=operator_id,
        created_by_username=operator_username or "operador",
        created_at=datetime.now(timezone.utc),
        source=(
            "assistant_assisted_drafting"
            if authorship_mode == "assisted_drafting"
            else "assistant_user_literal"
        ),
    )
    db.add(annotation)
    db.flush()
    return annotation
