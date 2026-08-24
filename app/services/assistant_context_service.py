"""
AT-05.1 — Contexto Investigativo Local v3

Seleção determinística de contexto investigativo local para o Assistente.
Somente leitura. Nenhuma escrita investigativa é executada aqui.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session, selectinload

from app.models.platea import SharedCase
from app.models.workspace import InvestigativeExcerpt, InvestigativeFinding, InvestigativeWorkspace
from app.services.report_archive_service import archive_context_text, search_report_archive


MAX_CONTEXT_CASES = 8
MAX_LIST_CASES = 25

EXPLICIT_CASE_REF_RE = re.compile(
    r"\bcaso\s+([A-Za-z0-9][A-Za-z0-9._/-]{2,})\b",
    re.IGNORECASE,
)


@dataclass
class InvestigativeContext:
    text: str
    sources: list[str]
    case_refs: list[str]


def _normalize(value: str | None) -> str:
    return (value or "").strip()


def _question_tokens(question: str) -> set[str]:
    tokens = re.findall(r"[A-Za-zÀ-ÿ0-9_-]+", question.lower())
    return {t for t in tokens if len(t) >= 4}


def _extract_explicit_case_ref(question: str) -> str | None:
    match = EXPLICIT_CASE_REF_RE.search(question)
    return match.group(1).strip(".,;:!?") if match else None


def _case_matches(case: SharedCase, question: str, tokens: set[str]) -> bool:
    q = question.lower()
    ref = _normalize(case.case_ref).lower()
    title = _normalize(case.title).lower()

    if ref and ref in q:
        return True

    title_tokens = {
        token
        for token in re.findall(r"[A-Za-zÀ-ÿ0-9_-]+", title)
        if len(token) >= 4
    }
    return bool(title_tokens & tokens)


def _format_person(person) -> str:
    parts = [f"nome={person.full_name}"]
    if person.person_ref:
        parts.append(f"ref={person.person_ref}")
    if person.aliases:
        parts.append(f"apelidos={person.aliases}")
    if person.cpf:
        parts.append(f"cpf={person.cpf}")
    if person.rg:
        parts.append(f"rg={person.rg}")
    if person.birth_date:
        parts.append(f"nascimento={person.birth_date}")
    if person.role_in_case:
        parts.append(f"papel={person.role_in_case}")
    if person.reliability_level:
        parts.append(f"confiabilidade={person.reliability_level}")
    if person.notes:
        parts.append(f"notas={person.notes}")
    return "; ".join(parts)


def _format_document(document) -> str:
    parts = [f"arquivo={document.filename}"]
    if document.document_ref:
        parts.append(f"ref={document.document_ref}")
    if document.file_type:
        parts.append(f"tipo={document.file_type}")
    if document.description:
        parts.append(f"descricao={document.description}")
    if document.sha256:
        parts.append(f"sha256={document.sha256}")
    return "; ".join(parts)


def _format_link(link) -> str:
    a = link.entity_a_name or link.entity_a_ref
    b = link.entity_b_name or link.entity_b_ref
    parts = [f"{a} -> {b}", f"tipo={link.link_type}"]
    if link.link_nature:
        parts.append(f"natureza={link.link_nature}")
    if link.notes:
        parts.append(f"notas={link.notes}")
    return "; ".join(parts)


def _serialize_case(case: SharedCase) -> str:
    lines = [
        f"[CASE:{case.case_ref}]",
        f"titulo: {case.title}",
        f"status: {case.status}",
    ]

    if case.classification:
        lines.append(f"classificacao: {case.classification}")
    if case.source_unit:
        lines.append(f"unidade_origem: {case.source_unit}")
    if case.published_by:
        lines.append(f"publicado_por: {case.published_by}")
    if case.published_at:
        lines.append(f"publicado_em: {case.published_at.isoformat()}")
    if case.last_updated_at:
        lines.append(f"atualizado_em: {case.last_updated_at.isoformat()}")
    if case.notes:
        lines.append(f"notas_do_caso: {case.notes}")
    if case.annotations:
        lines.append("anotacoes_humanas:")
        for annotation in case.annotations:
            lines.append(
                f"- [ANOTACAO:{annotation.id}] "
                f"autor={annotation.created_by_username}; "
                f"origem={annotation.source}; "
                f"conteudo={annotation.content}"
            )
    else:
        lines.append("anotacoes_humanas: nenhuma registrada")

    if case.persons:
        lines.append("pessoas:")
        lines.extend(f"- {_format_person(person)}" for person in case.persons)
    else:
        lines.append("pessoas: nenhuma registrada")

    if case.links:
        lines.append("vinculos:")
        lines.extend(f"- {_format_link(link)}" for link in case.links)
    else:
        lines.append("vinculos: nenhum registrado")

    if case.documents:
        lines.append("documentos:")
        lines.extend(f"- {_format_document(document)}" for document in case.documents)
    else:
        lines.append("documentos: nenhum registrado")

    return "\n".join(lines)


def _empty_context(message: str) -> InvestigativeContext:
    return InvestigativeContext(
        text=f"CONTEXTO INVESTIGATIVO LOCAL\n{message}",
        sources=[],
        case_refs=[],
    )


def build_investigative_context(
    db: Session,
    question: str,
    active_case_ref: str | None = None,
    operator_username: str | None = None,
) -> InvestigativeContext:
    cases = (
        db.query(SharedCase)
        .options(
            selectinload(SharedCase.persons),
            selectinload(SharedCase.documents),
            selectinload(SharedCase.links),
            selectinload(SharedCase.annotations),
        )
        .order_by(
            SharedCase.last_updated_at.desc(),
            SharedCase.published_at.desc(),
        )
        .limit(MAX_LIST_CASES)
        .all()
    )

    if not cases:
        return _empty_context("Nenhum caso está registrado na base investigativa local.")

    explicit_ref = _extract_explicit_case_ref(question)
    archive_results = [] if active_case_ref else search_report_archive(
        db, question, owner_username=operator_username, limit=8
    )

    # 1. Referência explícita do usuário tem prioridade máxima.
    if explicit_ref:
        exact = [
            case
            for case in cases
            if _normalize(case.case_ref).lower() == explicit_ref.lower()
        ]
        if not exact:
            return _empty_context(
                f"O caso solicitado ({explicit_ref}) nao foi encontrado na base investigativa local."
            )
        selected = exact[:1]

    # 2. Dentro do Workspace, o caso ativo é o escopo padrão.
    elif active_case_ref:
        active = [
            case
            for case in cases
            if _normalize(case.case_ref).lower() == active_case_ref.lower()
        ]
        if not active:
            return _empty_context(
                f"O caso ativo ({active_case_ref}) nao foi encontrado na base investigativa local."
            )
        selected = active[:1]

    elif archive_results:
        archive_case_ids = [item[0].shared_case_id for item in archive_results][:MAX_CONTEXT_CASES]
        archived_cases = (
            db.query(SharedCase)
            .options(
                selectinload(SharedCase.persons),
                selectinload(SharedCase.documents),
                selectinload(SharedCase.links),
                selectinload(SharedCase.annotations),
            )
            .filter(SharedCase.id.in_(archive_case_ids))
            .all()
        )
        archived_by_id = {case.id: case for case in archived_cases}
        selected = [archived_by_id[item_id] for item_id in archive_case_ids if item_id in archived_by_id]

    else:
        q = question.lower()

        # 2. Consultas de estado/status têm precedência sobre similaridade textual.
        asks_open = any(
            term in q
            for term in (
                "casos abertos",
                "caso aberto",
                "estao abertos",
                "estão abertos",
                "em andamento",
            )
        )

        if asks_open:
            selected = [
                case
                for case in cases
                if _normalize(case.status).lower() == "aberto"
            ][:MAX_CONTEXT_CASES]

        else:
            # 3. Só depois usamos correspondência por título/ref.
            tokens = _question_tokens(question)
            matched = [
                case
                for case in cases
                if _case_matches(case, question, tokens)
            ]

            if matched:
                selected = matched[:MAX_CONTEXT_CASES]
            else:
                # Pergunta investigativa genérica: janela limitada dos mais recentes.
                selected = cases[:MAX_CONTEXT_CASES]

    if not selected:
        return _empty_context(
            "A consulta nao encontrou registros compativeis na base investigativa local."
        )

    sources = [f"CASE:{case.case_ref}" for case in selected]
    text = (
        "CONTEXTO INVESTIGATIVO LOCAL — SOMENTE LEITURA\n"
        "Use somente os registros abaixo para afirmacoes especificas sobre "
        "casos, pessoas, documentos ou vinculos. Cada bloco inicia com sua fonte.\n\n"
        + "\n\n".join(_serialize_case(case) for case in selected)
    )

    # AT06B1_ANALYTICAL_CORE_V1 — Achados validados passam a integrar o contexto local.
    finding_sections: list[str] = []
    for case in selected:
        workspace = (
            db.query(InvestigativeWorkspace)
            .filter(InvestigativeWorkspace.shared_case_id == case.id)
            .first()
        )
        if not workspace:
            continue
        findings = (
            db.query(InvestigativeFinding)
            .options(
                selectinload(InvestigativeFinding.excerpt)
                .selectinload(InvestigativeExcerpt.sources)
            )
            .filter(
                InvestigativeFinding.workspace_id == workspace.id,
                InvestigativeFinding.status == "validated",
            )
            .order_by(InvestigativeFinding.validated_at.asc(), InvestigativeFinding.id.asc())
            .all()
        )
        if not findings:
            continue

        lines = [
            f"ACHADOS INVESTIGATIVOS VALIDADOS DO CASO {case.case_ref}",
            "Regra: respeite o tipo epistemológico de cada Achado. "
            "Inferência e hipótese não devem ser apresentadas como fato.",
        ]
        for finding in findings:
            marker = f"ACHADO:{finding.id}"
            sources.append(marker)
            lines.append(
                f"- [{marker}] tipo={finding.finding_type}; titulo={finding.title}; "
                f"resumo_objetivo={finding.objective_summary}; "
                f"interpretacao={finding.interpretation or 'nenhuma'}; "
                f"validado_por={finding.validated_by_username}"
            )
            if finding.excerpt and finding.excerpt.sources:
                source_labels = "; ".join(
                    source.source_label_snapshot for source in finding.excerpt.sources
                )
                lines.append(f"  fontes_do_recorte={source_labels}")
        finding_sections.append("\n".join(lines))

    if finding_sections:
        text += "\n\n" + "\n\n".join(finding_sections)

    if archive_results:
        archive_text, archive_sources, _ = archive_context_text(archive_results)
        if archive_text:
            text += "\n\n" + archive_text
            sources.extend(item for item in archive_sources if item not in sources)

    return InvestigativeContext(
        text=text,
        sources=sources,
        case_refs=[case.case_ref for case in selected],
    )
