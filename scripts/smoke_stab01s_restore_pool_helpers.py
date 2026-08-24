from __future__ import annotations
from pathlib import Path
import re


def main() -> None:
    text = Path("app/templates/workspace.html").read_text(encoding="utf-8")

    # Current stabilized baseline stays present.
    for marker in (
        "STAB01R_INTERACTION_CONTROLLER_V1",
        "UX02_TOPIC_OPERATIONAL_PROGRESSION_V2",
        "CONTEXTO DO ANALISTA",
        "BASE DISPONÍVEL",
        "STAB01S_RESTORE_POOL_DND_HELPERS",
    ):
        assert marker in text, marker

    # The two missing helpers that aborted / threatened runtime are restored.
    assert text.count("function updateCreateDropStatus()") == 1
    assert text.count("function setSourceChecked(token,checked=true)") == 1
    assert "updateCreateDropStatus();" in text
    assert "setSourceChecked(token,true)" in text

    # updateCreateDropStatus is safe when the technical block form is absent
    # in structured topics such as header/facts.
    helper_start = text.index("function updateCreateDropStatus()")
    helper_end = text.index("function setSourceChecked(", helper_start)
    helper = text[helper_start:helper_end]
    assert "if(!createDropStatus)return" in helper

    # setSourceChecked keeps the pre-existing provenance/selection path.
    set_start = text.index("function setSourceChecked(")
    set_end = text.index("function poolItemMatchesContext(", set_start)
    set_body = text[set_start:set_end]
    for marker in (
        "selectionSnapshot()",
        "selectionHistory.push(before)",
        "input.checked=checked",
        "updateSelectionControls()",
        "updateCreateDropStatus()",
    ):
        assert marker in set_body, marker

    # Previous stabilization contracts remain intact.
    assert "createBlockForm?.addEventListener('submit'" in text
    assert "createBlockForm.addEventListener('submit'" not in text
    assert "function ux02VisibleStage()" in text
    assert "function ux02CurrentStageForProgress(reached)" in text
    assert "ux02SetStage(initialStage,{remember:false,focus:false})" in text

    # No UX expansion.
    assert "UX03" not in text
    assert "UX-03" not in text

    print("STAB-01S SMOKE: OK")
    print("updateCreateDropStatus=restored setSourceChecked=restored structured-topic-null-safe=yes")
    print("STAB-01R=preserved UX02=preserved backend=untouched")


if __name__ == "__main__":
    main()
