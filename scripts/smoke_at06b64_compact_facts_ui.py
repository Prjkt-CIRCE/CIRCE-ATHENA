from __future__ import annotations

from pathlib import Path


def main() -> None:
    text = Path("app/templates/workspace.html").read_text(encoding="utf-8")

    required = (
        "AT06B64_COMPACT_FACT_WORKBENCH_V1",
        "Dados estruturados",
        "Síntese documental",
        "Contexto e delimitação do analista",
        "Confirmar mapa factual",
        "fact-status-badge",
        "fact-row__excerpt-toggle",
        "syncFactRowState",
        "confirmando mapa factual",
    )
    for marker in required:
        assert marker in text, marker

    assert "Confirmar itens preenchidos" not in text
    assert "{% if not active_topic or active_topic.topic_key not in ['header','facts'] %}" in text

    print("AT-06B6.4 SMOKE: OK")
    print("facts=compact details=ondemand provenance=compact review=single-action")


if __name__ == "__main__":
    main()
