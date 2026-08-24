from __future__ import annotations
from pathlib import Path


def function_body(text: str, name: str) -> str:
    marker = f"function {name}("
    start = text.index(marker)
    paren = text.index("(", start)
    depth = 0
    close_paren = None
    quote = None
    escape = False
    for idx in range(paren, len(text)):
        ch = text[idx]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                close_paren = idx
                break
    assert close_paren is not None, name
    brace = text.index("{", close_paren)
    depth = 0
    quote = None
    escape = False
    for idx in range(brace, len(text)):
        ch = text[idx]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1:idx]
    raise AssertionError(f"Função sem fechamento: {name}")


def main() -> None:
    text = Path("app/templates/workspace.html").read_text(encoding="utf-8")

    # Current approved UX must remain present.
    for marker in (
        "UX01_WORKSPACE_SPATIAL_HIERARCHY_V1_1",
        "UX02_TOPIC_OPERATIONAL_PROGRESSION_V2",
        "UX02_2_WORKSPACE_ID_INIT_ORDER",
        "DELIMITAÇÃO SUGERIDA",
        "CONTEXTO DO ANALISTA",
        "BASE DISPONÍVEL",
        "Pronto para compor a primeira versão.",
        "STAB01R_INTERACTION_CONTROLLER_V1",
    ):
        assert marker in text, marker

    # Previous runtime fix remains intact.
    assert "createBlockForm?.addEventListener('submit'" in text
    assert "createBlockForm.addEventListener('submit'" not in text

    # R1: progress refresh can update labels/states, never switch panels.
    progress = function_body(text, "updateUx02Progress")
    assert "panel.hidden" not in progress
    assert ".hidden=" not in progress

    # R3: explicit navigation is the sole stage visibility owner.
    set_stage = function_body(text, "ux02SetStage")
    assert "panel.hidden=panel.dataset.ux02Panel!==stage" in set_stage
    assert "const reached=ux02ReachedStages();if(!reached[stage])return" in set_stage
    assert "ux02WritePreferredStage(stage)" in set_stage
    assert "ux02StageTabs.forEach(button=>button.addEventListener('click'" in text

    # R1: editing listeners remain registered.
    assert "row.querySelector('.fact-value')?.addEventListener('input'" in text
    assert "row.querySelector('.fact-status-select')?.addEventListener('change'" in text
    assert "factsAnalystContext?.addEventListener('input'" in text

    # R2: all Dos Fatos persistence calls use the early-safe workspace id.
    for suffix in (
        "/facts/save",
        "/facts/extract",
        "/narrative/compose",
        "/narrative/save",
        "/composition/confirm",
    ):
        good = f"'/api/workspaces/'+ux02WorkspaceId+'/topics/'+activeTopicId+'{suffix}'"
        bad = f"'/api/workspaces/'+workspaceId+'/topics/'+activeTopicId+'{suffix}'"
        assert good in text, good
        assert bad not in text, bad

    # Explicit one-time initialization owns initial visibility.
    assert "const initialStage=ux02ReadPreferredStage()||ux02DerivedStage()" in text
    assert "ux02SetStage(initialStage,{remember:false,focus:false})" in text

    # Stabilization must not introduce next UX.
    assert "UX03" not in text
    assert "UX-03" not in text

    print("STAB-01R SMOKE: OK")
    print("R1=focus-panel-decoupled R2=facts-persistence-safe-id R3=explicit-stage-return")
    print("UX02-context-to-narrative=preserved")


if __name__ == "__main__":
    main()
