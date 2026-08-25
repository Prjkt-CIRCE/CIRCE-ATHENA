"""AT-06B-CURATED-01 G5 smoke: Workspace intake UI contract."""

from pathlib import Path


def main() -> None:
    path = Path("app/templates/workspace.html")
    text = path.read_text(encoding="utf-8-sig")

    required = [
        'id="case-documents-section"',
        'id="document-intake-trigger"',
        'id="document-intake-input"',
        'id="document-intake-feedback"',
        'INCORPORAR MATERIAL',
        'INCORPORANDO…',
        'DISPONÍVEL',
        'METADADOS',
        '/api/documents/{{ item.id }}/original',
        "new FormData()",
        "Documento já existe neste Caso.",
        "window.location.reload()",
        'accept=".pdf,.png,.jpg,.jpeg,.txt,.csv,.docx,.xlsx"',
        'value="document:{{ item.id }}"',
        'form="create-block-form"',
    ]

    for marker in required:
        assert marker in text, f"Marcador ausente: {marker}"

    # Estrutura física interna nunca deve aparecer na UI.
    assert "{{ item.storage_relpath }}" not in text

    # A recuperação do original deve depender de disponibilidade física.
    assert "{% if item.physical_available %}" in text

    # Um bloco CSS e um bloco JS desta unidade.
    assert (
        text.count(
            "/* AT06B_CURATED_01_DOCUMENT_INTAKE_UI */"
        )
        == 1
    )

    assert (
        text.count(
            "// AT06B_CURATED_01_DOCUMENT_INTAKE_UI"
        )
        == 1
    )

    print("AT-06B-CURATED-01 WORKSPACE UI SMOKE: OK")
    print("intake-action=present")
    print("native-file-picker=present")
    print("working-feedback=present")
    print("available-state=present")
    print("metadata-only-state=present")
    print("original-retrieval=governed-route")
    print("storage-relpath=not-exposed")
    print("block-source-selection=preserved")


if __name__ == "__main__":
    main()
