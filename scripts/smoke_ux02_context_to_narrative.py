from __future__ import annotations
from pathlib import Path


def main() -> None:
    text = Path("app/templates/workspace.html").read_text(encoding="utf-8")

    required = (
        # Baseline aprovado.
        "UX01_WORKSPACE_SPATIAL_HIERARCHY_V1_1",
        "UX02_TOPIC_OPERATIONAL_PROGRESSION_V2",
        "UX02_2_WORKSPACE_ID_INIT_ORDER",
        "createBlockForm?.addEventListener('submit'",
        "Revisar mapa factual",
        "ux02MapCountText",

        # Contexto -> Narrativa.
        "BASE DA ANÁLISE",
        "ux02-context-source-count",
        "ux02-context-fact-count",
        "DELIMITAÇÃO SUGERIDA",
        "Sugestão assistida",
        "CONTEXTO DO ANALISTA",
        "AUTORIA: ANALISTA",
        "Registre observações, delimitações ou orientações necessárias para a construção da narrativa.",
        "ux02ContextDraftPresent",
        "ux02ContextPersisted",
        "ux02ContextSaved",
        "narrative:contextSaved||reviewReady",
        "Contexto salvo.",
        "ux02-context-complete-summary",
        "Contexto registrado",
        "BASE DISPONÍVEL",
        "Pronto para compor a primeira versão.",
        "Compor primeira versão",
    )
    for marker in required:
        assert marker in text, marker

    # A proposta assistida não pode estar sob autoria humana global.
    context_pos = text.index('data-ux02-panel="context"')
    narrative_pos = text.index('data-ux02-panel="narrative"')
    context = text[context_pos:narrative_pos]
    assert context.index("DELIMITAÇÃO SUGERIDA") < context.index("AUTORIA: ANALISTA")
    assert "contexto humano{% endif %}" not in context

    # Narrativa só fica alcançável quando Contexto está salvo/persistido.
    assert "narrative:mapConfirmed||reviewReady" not in text
    assert "narrative:contextSaved||reviewReady" in text

    # Não há composição automática nesta rodada.
    assert "factsCompose.click()" not in text
    assert ".click();ux02SetStage('review'" not in text

    # Não avançar Revisão/UX-03.
    assert "UX03" not in text
    assert "UX-03" not in text

    # Infraestrutura preservada.
    for marker in (
        "bindSplitter(splitterContext,'context')",
        "bindSplitter(splitterAthena,'athena')",
        'data-detach-pane="pool"',
        'data-detach-pane="work"',
        'data-detach-pane="athena"',
        "localPoolSelectionTokens",
        "BANDEJA DA MESA",
        "pool-browser-modal",
        "window.__athenaWorkspaceChannel",
        "AT06B64_COMPACT_FACT_WORKBENCH_V1",
        "fact-row__excerpt-toggle",
        "syncFactRowState",
    ):
        assert marker in text, marker

    print("UX-02 CONTEXTO -> NARRATIVA SMOKE: OK")
    print("base=compact proposal!=analyst context=human save=>narrative context-summary=ok composition=not-executed")


if __name__ == "__main__":
    main()
