"""
AT-05.6 — Planejador conversacional com contexto de ação recente.

Mantém distinção entre:
- histórico textual;
- caso ativo;
- artefato/ação recente explicitamente retornado pelo backend.

O contexto recente é usado para resolver referências como:
"essa observação", "essa anotação", "o que você acabou de registrar".
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

import httpx

from app.config import settings


WRITE_HINT_RE = re.compile(
    r"\b("
    r"anot|registr|adic|inclu|acresc|coloc|salv|guarde|"
    r"corrig|alter|mude|atualiz|remov|exclu|apag|"
    r"redij|reescrev|melhor|fundament|desenvolv|detalh|densific"
    r")",
    re.IGNORECASE,
)

DRAFTING_HINT_RE = re.compile(
    r"\b("
    r"redij|reescrev|melhor|aperfei[cç]o|fundament|desenvolv|"
    r"detalh|densific|robust|t[eé]cnic|formaliz|estrutur"
    r")",
    re.IGNORECASE,
)

RECENT_ANNOTATION_PHRASES = (
    "essa observação",
    "essa anotação",
    "esse texto",
    "isso que você registrou",
    "isso que voce registrou",
    "isso que você acabou de registrar",
    "isso que voce acabou de registrar",
    "o que você acabou de registrar",
    "o que voce acabou de registrar",
    "a anterior",
)


LITERAL_CONTENT_PATTERNS = (
    re.compile(
        r"\b(?:dizendo|informando|registrando|consignando)\s+que\s+(.+)$",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:anote|registre|adicione|inclua|acrescente)\b.*?:\s*(.+)$",
        re.IGNORECASE | re.DOTALL,
    ),
)

AuthorshipMode = Literal["literal", "assisted_drafting"]


@dataclass
class PlannedAction:
    action_type: str
    case_ref: str | None
    content: str | None
    authorship_mode: AuthorshipMode | None = None
    explanation: str | None = None


def may_contain_write_intent(text: str) -> bool:
    return bool(WRITE_HINT_RE.search(text or ""))


def requests_assisted_drafting(text: str) -> bool:
    return bool(DRAFTING_HINT_RE.search(text or ""))


def refers_to_recent_annotation(text: str) -> bool:
    """
    Resolve referências conversacionais simples a uma anotação recente.

    A comparação deliberadamente usa frases normalizadas em vez de uma regex
    ampla, porque aqui queremos previsibilidade e fácil extensão.
    """
    normalized = " ".join((text or "").strip().lower().split())
    return any(phrase in normalized for phrase in RECENT_ANNOTATION_PHRASES)


def extract_literal_annotation_content(message: str) -> str | None:
    value = (message or "").strip()

    for pattern in LITERAL_CONTENT_PATTERNS:
        match = pattern.search(value)
        if match:
            content = match.group(1).strip()
            if content:
                return content

    return None


def _extract_json_object(text: str) -> dict | None:
    if not text:
        return None

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None

    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize_recent_action(recent_action: dict | None) -> dict | None:
    if not isinstance(recent_action, dict):
        return None

    action_type = recent_action.get("type")
    case_ref = recent_action.get("case_ref")
    content = recent_action.get("content")
    annotation_id = recent_action.get("annotation_id")

    if action_type != "case_annotation":
        return None

    if not isinstance(case_ref, str) or not case_ref.strip():
        return None

    if not isinstance(content, str) or not content.strip():
        return None

    return {
        "type": "case_annotation",
        "case_ref": case_ref.strip(),
        "content": content.strip(),
        "annotation_id": annotation_id,
    }


async def plan_user_action(
    *,
    message: str,
    active_case_ref: str | None,
    recent_history: list[dict] | None = None,
    recent_action: dict | None = None,
) -> PlannedAction:
    history_text = ""
    for item in (recent_history or [])[-6:]:
        role = item.get("role", "")
        content = (item.get("content") or "")[:800]
        if role in {"user", "assistant"} and content:
            history_text += f"{role}: {content}\n"

    normalized_recent = _normalize_recent_action(recent_action)

    deterministic_authorship = (
        "assisted_drafting"
        if requests_assisted_drafting(message)
        else "literal"
    )

    recent_annotation_text = "(nenhuma)"
    if normalized_recent:
        recent_annotation_text = (
            f"tipo=case_annotation\n"
            f"case_ref={normalized_recent['case_ref']}\n"
            f"annotation_id={normalized_recent.get('annotation_id')}\n"
            f"content={normalized_recent['content']}"
        )

    planner_prompt = f"""
Você é um planejador interno de ações do Assistente de Inteligência ATHENA.

Retorne SOMENTE JSON válido. Não responda ao usuário fora do JSON.

Ações permitidas:
1. add_case_annotation
2. unsupported_write
3. none

MODOS DE AUTORIA:
- literal: registrar somente conteúdo explicitamente ditado pelo operador.
- assisted_drafting: o operador pediu explicitamente que Athena redija,
  melhore, fundamente, densifique, detalhe ou estruture o texto.

AUTHORSHIP_HINT={deterministic_authorship}

CONTEXTO DE AÇÃO RECENTE:
{recent_annotation_text}

Se a mensagem disser "essa observação", "essa anotação", "esse texto",
"o que você acabou de registrar" ou equivalente, use o artefato recente
acima somente se ele existir.

Se o pedido for assisted_drafting sobre a anotação recente:
- use o conteúdo recente como matéria-prima;
- preserve o sentido factual;
- não invente fatos novos;
- produza uma versão redigida adequada ao pedido;
- use o case_ref da anotação recente caso a mensagem não indique outro.

ACTIVE_CASE_REF: {active_case_ref or "null"}

Histórico recente:
{history_text or "(sem histórico)"}

Mensagem:
{message}

Formato:
{{
  "action_type": "add_case_annotation|unsupported_write|none",
  "case_ref": "referência ou null",
  "content": "texto autorizado/proposto ou null",
  "authorship_mode": "literal|assisted_drafting|null",
  "explanation": "frase curta apenas para unsupported_write ou null"
}}
""".strip()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "system", "content": planner_prompt}],
                    "temperature": 0.0,
                    "max_tokens": 650,
                },
                headers={"Authorization": "Bearer lm-studio"},
            )
            response.raise_for_status()

        raw = response.json()["choices"][0]["message"]["content"]

    except Exception:
        return PlannedAction("none", None, None, None)

    parsed = _extract_json_object(raw)
    if not parsed:
        return PlannedAction("none", None, None, None)

    action_type = str(parsed.get("action_type") or "none").strip()
    if action_type not in {"add_case_annotation", "unsupported_write", "none"}:
        action_type = "none"

    case_ref = parsed.get("case_ref")
    case_ref = (
        case_ref.strip()
        if isinstance(case_ref, str) and case_ref.strip()
        else None
    )

    content = parsed.get("content")
    content = (
        content.strip()
        if isinstance(content, str) and content.strip()
        else None
    )

    authorship_mode: AuthorshipMode | None = None

    if action_type == "add_case_annotation":
        authorship_mode = deterministic_authorship

        # Referência ao artefato recente tem precedência quando explícita.
        if normalized_recent and refers_to_recent_annotation(message):
            if not case_ref:
                case_ref = normalized_recent["case_ref"]

        if not case_ref and active_case_ref:
            case_ref = active_case_ref

        if authorship_mode == "literal":
            literal_content = extract_literal_annotation_content(message)
            content = literal_content if literal_content else None

        elif authorship_mode == "assisted_drafting":
            # Quando o pedido é sobre "essa observação", o LLM pode redigir
            # a partir do texto recente, mas nunca criar fatos novos.
            if refers_to_recent_annotation(message) and not normalized_recent:
                return PlannedAction(
                    action_type="unsupported_write",
                    case_ref=case_ref,
                    content=None,
                    authorship_mode=authorship_mode,
                    explanation=(
                        "Entendi que você se refere a uma anotação recente, "
                        "mas não há uma anotação recente disponível nesta sessão."
                    ),
                )

        if not case_ref or not content:
            return PlannedAction(
                action_type="unsupported_write",
                case_ref=case_ref,
                content=content,
                authorship_mode=authorship_mode,
                explanation=(
                    "Entendi que você quer registrar uma anotação, mas não consegui "
                    "determinar com segurança o caso e o conteúdo autorizado."
                ),
            )

    explanation = parsed.get("explanation")
    explanation = (
        explanation.strip()
        if isinstance(explanation, str) and explanation.strip()
        else None
    )

    return PlannedAction(
        action_type=action_type,
        case_ref=case_ref,
        content=content,
        authorship_mode=authorship_mode,
        explanation=explanation,
    )
