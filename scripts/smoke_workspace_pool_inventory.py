"""UX-02A smoke: canonical Case inventory inside the Workspace Pool."""

from pathlib import Path


template = Path("app/templates/workspace.html").read_text(
    encoding="utf-8-sig"
)

start_marker = "<!-- UX02A_POOL_INVENTORY_START -->"
end_marker = "<!-- UX02A_POOL_INVENTORY_END -->"
css_marker = "/* UX02A_POOL_INVENTORY_V1"
js_marker = "// UX02A_POOL_INVENTORY_V1"

assert template.count(start_marker) == 1
assert template.count(end_marker) == 1
assert template.count(css_marker) == 1
assert template.count(js_marker) == 1

pool = template.split(start_marker, 1)[1].split(end_marker, 1)[0]
pool_css = template.split(css_marker, 1)[1].split("</style>", 1)[0]

required_pool = {
    "title": "ACERVO DO CASO",
    "real-total": (
        "{% set pool_total = persons|length + documents|length + "
        "links|length + annotations|length %}"
    ),
    "total-output": 'id="pool-inventory-total">{{ pool_total }} MATERIAIS',
    "intake-action": 'id="document-intake-trigger"',
    "intake-label": "INCORPORAR MATERIAL",
    "intake-picker": 'id="document-intake-input"',
    "intake-feedback": 'id="document-intake-feedback"',
    "search": 'id="pool-inventory-search"',
    "family-filter": 'id="pool-family-filter"',
    "family-all": '<option value="all">Todos</option>',
    "family-documents": '<option value="document">Documentos</option>',
    "family-persons": '<option value="person">Pessoas</option>',
    "family-links": '<option value="link">V&iacute;nculos</option>',
    "family-annotations": '<option value="annotation">Anota&ccedil;&otilde;es</option>',
    "document-filter": 'id="pool-document-filter"',
    "document-all": '<option value="all">Todos os documentos</option>',
    "document-original": '<option value="original">Com Original</option>',
    "document-metadata": '<option value="metadata">Somente metadados</option>',
    "persons-group": 'data-pool-family="person"',
    "documents-group": 'data-pool-family="document"',
    "links-group": 'data-pool-family="link"',
    "annotations-group": 'data-pool-family="annotation"',
    "inventory-structure": 'class="pool-inventory-list"',
    "inventory-item": 'class="pool-inventory-item"',
    "selection-mode": 'id="pool-selection-mode-toggle"',
    "selection-label": "SELECIONAR PARA A MESA",
    "selection-bar": 'id="context-selection-bar"',
    "selection-undo": 'id="undo-selection"',
    "selection-clear": 'id="clear-selection"',
    "document-id": 'data-document-id="{{ item.id }}"',
    "storage-state": 'data-storage-state="{{ item.storage_state }}"',
    "original-route": '/api/documents/{{ item.id }}/original',
    "metadata-only-state": "SOMENTE METADADOS",
}

missing_pool = [
    name for name, marker in required_pool.items()
    if marker not in pool
]

required_template = {
    "canonical-intake": (
        "/api/cases/'+encodeURIComponent(caseRef)+'/documents/intake"
    ),
    "document-source": 'value="document:{{ item.id }}"',
    "person-source": 'value="person:{{ item.id }}"',
    "link-source": 'value="link:{{ item.id }}"',
    "annotation-source": 'value="annotation:{{ item.id }}"',
    "block-form-contract": 'form="create-block-form"',
    "pool-collapse": 'id="toggle-context-pane"',
    "context-splitter": 'id="splitter-context"',
    "resize-contract": "AT06A_RESIZABLE_TILING_V1",
    "layout-storage": "circe-athena.workspace.layout.v3",
    "collapse-storage": "circe-athena.workspace.collapse.v2",
    "filter-function": "function applyPoolInventoryFilters()",
    "search-listener": (
        "poolInventorySearch?.addEventListener('input',"
        "applyPoolInventoryFilters)"
    ),
    "family-listener": (
        "poolFamilyFilter?.addEventListener('change',"
        "applyPoolInventoryFilters)"
    ),
    "document-listener": (
        "poolDocumentFilter?.addEventListener('change',"
        "applyPoolInventoryFilters)"
    ),
    "real-document-types": "function populateDocumentTypeFilters()",
    "selection-encapsulation": "function setPoolSelectionMode(active)",
}

missing_template = [
    name for name, marker in required_template.items()
    if marker not in template
]

legacy_pool = [
    marker for marker in ("context-section", "context-item")
    if marker in pool
]

forbidden_implementation = {
    "new-pool-endpoint": "/api/pool",
    "new-material-endpoint": "/api/materials",
    "storage-path": "storage_relpath",
    "direct-storage": "LocalCaseStorage",
    "smart-bin": "Smart Bin",
    "ocr": "OCR",
    "cellebrite": "Cellebrite",
    "ai-classification": "classificação por IA",
}

forbidden_found = [
    name for name, marker in forbidden_implementation.items()
    if marker.lower() in template.lower()
]

assert ".workspace-page #pane-context" in pool_css
assert "rgba(95,179,207" not in pool_css
for event_name in ("dragenter", "dragover", "dragleave", "drop"):
    listener = f".addEventListener('{event_name}'"
    assert template.count(listener) == 1
    assert f"poolIntakeDropzone?{listener}" in template

assert "dataTransfer" in template
for global_target in ("document", "window", "document.body"):
    for event_name in ("dragenter", "dragover", "dragleave", "drop"):
        assert (
            f"{global_target}.addEventListener('{event_name}'"
            not in template
        )

if missing_pool or missing_template or legacy_pool or forbidden_found:
    details = []
    if missing_pool:
        details.append("missing-pool=" + ",".join(missing_pool))
    if missing_template:
        details.append("missing-template=" + ",".join(missing_template))
    if legacy_pool:
        details.append("legacy-pool=" + ",".join(legacy_pool))
    if forbidden_found:
        details.append("forbidden=" + ",".join(forbidden_found))
    raise SystemExit(
        "UX-02A WORKSPACE POOL INVENTORY SMOKE: FAIL -> "
        + " | ".join(details)
    )

print("UX-02A WORKSPACE POOL INVENTORY SMOKE: OK")
print("canonical-families=4")
print("real-counts=yes")
print("deterministic-client-filters=yes")
print("document-types=real-data-only")
print("mesa-selection=explicit-mode")
print("canonical-intake=preserved")
print("governed-original=preserved")
print("legacy-pool-dom=no")
print("drag-and-drop=pool-intake-local-only")
