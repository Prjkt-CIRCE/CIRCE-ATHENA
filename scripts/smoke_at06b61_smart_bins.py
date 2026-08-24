from __future__ import annotations

from pathlib import Path


def main() -> None:
    workspace = Path("app/templates/workspace.html").read_text(encoding="utf-8")
    route = Path("app/routes/workspace.py").read_text(encoding="utf-8")

    required = (
        "Usados no tópico",
        "Ainda não usados",
        "data-pool-import-bin=\"documents\"",
        "Importar arquivos nesta Bin",
        "visibleSelectedSourceTokens",
        "AT06B61_BIN_DIRECT_IMPORT_V1",
        "active_topic_used_source_tokens",
    )
    for marker in required:
        assert marker in workspace or marker in route, marker

    assert ">Seleção atual<" not in workspace
    assert "+ Adicionar material" not in workspace
    assert "bin_hint" in route
    assert 'allowed_manual_bins = {"persons", "documents", "images", "audio", "video"}' in route

    print("AT-06B6.1 SMOKE: OK")
    print("smart_bins=context/used/unused/assistant-notes selection_scope=view import=bin")


if __name__ == "__main__":
    main()
