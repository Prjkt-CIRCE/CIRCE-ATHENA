"""AT-06B-CURATED-01 G5 smoke: Workspace intake UI contract.

This smoke intentionally validates structural/behavioral contracts,
not user-facing wording. Visual labels may change during redesign
without invalidating the AT-06B domain contract.
"""

from pathlib import Path


def main() -> None:
    path = Path("app/templates/workspace.html")
    text = path.read_text(encoding="utf-8-sig")

    required = [
        # Document section / native picker
        'id="case-documents-section"',
        'id="document-intake-trigger"',
        'id="document-intake-input"',
        'id="document-intake-feedback"',
        'accept=".pdf,.png,.jpg,.jpeg,.txt,.csv,.docx,.xlsx"',

        # Existing block-source selection contract
        'value="document:{{ item.id }}"',
        'form="create-block-form"',

        # Physical-state presentation contract
        'data-storage-state="{{ item.storage_state }}"',
        "document-state--available",
        "document-state--metadata",
        "{% if item.physical_available %}",

        # Governed retrieval
        '/api/documents/{{ item.id }}/original',

        # Intake behavior
        "new FormData()",
        "documentIntakeTrigger.disabled=true",
        "setDocumentIntakeFeedback(",
        "'working'",
        "payload?.status==='duplicate'",
        "payload?.status==='hydrated'",
        "window.location.reload()",

        # Unit markers
        "/* AT06B_CURATED_01_DOCUMENT_INTAKE_UI */",
        "// AT06B_CURATED_01_DOCUMENT_INTAKE_UI",
    ]

    for marker in required:
        assert marker in text, f"Marcador ausente: {marker}"

    # Storage internals must never be rendered in the browser.
    assert "{{ item.storage_relpath }}" not in text

    # Exactly one CSS and one JS unit for this integration.
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
    print("working-state=present")
    print("available-state=structural")
    print("metadata-state=structural")
    print("duplicate-path=present")
    print("hydration-path=present")
    print("original-retrieval=governed-route")
    print("storage-relpath=not-exposed")
    print("block-source-selection=preserved")


if __name__ == "__main__":
    main()
