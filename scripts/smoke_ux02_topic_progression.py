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

    for marker in (
        "UX02_TOPIC_OPERATIONAL_PROGRESSION_V2",
        "UX02_2_WORKSPACE_ID_INIT_ORDER",
        'data-ux02-stage="sources"',
        'data-ux02-stage="map"',
        'data-ux02-stage="context"',
        'data-ux02-stage="narrative"',
        'data-ux02-stage="review"',
        "ux02ReachedStages",
        "ux02DerivedStage",
        "ux02SetStage",
        "ux02ReadPreferredStage",
        "ux02WritePreferredStage",
        "ux02StageTabs.forEach(button=>button.addEventListener('click'",
    ):
        assert marker in text, marker

    progress = function_body(text, "updateUx02Progress")
    assert "panel.hidden" not in progress
    assert ".hidden=" not in progress

    set_stage = function_body(text, "ux02SetStage")
    assert "panel.hidden=panel.dataset.ux02Panel!==stage" in set_stage
    assert "const reached=ux02ReachedStages();if(!reached[stage])return" in set_stage
    assert "ux02WritePreferredStage(stage)" in set_stage

    assert "const initialStage=ux02ReadPreferredStage()||ux02DerivedStage()" in text
    assert "ux02SetStage(initialStage,{remember:false,focus:false})" in text

    compact = text.replace(" ", "")
    assert "map:mapReady" in compact
    assert "context:mapConfirmed||reviewReady" in compact
    assert "narrative:contextSaved||reviewReady" in compact

    assert "document.querySelectorAll('[data-topic-status]')" not in text
    assert "document.querySelectorAll('button[data-topic-status]')" in text
    assert "createBlockForm?.addEventListener('submit'" in text
    assert "createBlockForm.addEventListener('submit'" not in text

    print("UX-02 TOPIC PROGRESSION SMOKE: OK")
    print("stage-navigation=explicit progress-refresh=non-navigating revisit=preserved STAB01=compatible")


if __name__ == "__main__":
    main()
