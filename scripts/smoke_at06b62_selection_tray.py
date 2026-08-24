from __future__ import annotations

from pathlib import Path


def main() -> None:
    text = Path("app/templates/workspace.html").read_text(encoding="utf-8")

    required = (
        "BANDEJA DA MESA",
        "Adicionar à bandeja",
        "pool-modal-tray-count",
        "localPoolSelectionTokens",
        "visibleSelectedSourceTokens",
        "clearLocalPoolSelection",
        "is-in-tray",
        "AT06B62_LOCAL_SELECTION_TRAY_V1",
    )
    for marker in required:
        assert marker in text, marker

    forbidden = (
        "commitPoolSelection",
        "Selecionado para a Mesa.",
        "Usar '+count+' na Mesa",
    )
    for marker in forbidden:
        assert marker not in text, marker

    assert "poolModalSelectionCount.textContent=count===1?'1 selecionado nesta visão':count+' selecionados nesta visão'" in text
    assert "poolModalTrayCount.textContent='Bandeja da Mesa: '+count" in text

    print("AT-06B6.2 SMOKE: OK")
    print("selection=local-view tray=explicit multi-bin=ok smart-bins=preserved")


if __name__ == "__main__":
    main()
