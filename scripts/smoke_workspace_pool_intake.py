"""UX-02B smoke: local interactive Intake inside the Workspace Pool."""

import re
from pathlib import Path


template = Path("app/templates/workspace.html").read_text(
    encoding="utf-8-sig"
)

pool_start = "<!-- UX02A_POOL_INVENTORY_START -->"
pool_end = "<!-- UX02A_POOL_INVENTORY_END -->"
drop_start = "<!-- UX02B_POOL_INTAKE_START -->"
drop_end = "<!-- UX02B_POOL_INTAKE_END -->"
css_marker = "/* UX02B_POOL_INTAKE_V1"
js_marker = "// UX02B_POOL_INTAKE_V1"

assert template.count(drop_start) == 1
assert template.count(drop_end) == 1
assert template.count(css_marker) == 1
assert template.count(js_marker) == 1

pool = template.split(pool_start, 1)[1].split(pool_end, 1)[0]
drop_markup = template.split(drop_start, 1)[1].split(drop_end, 1)[0]
intake_css = template.split(css_marker, 1)[1].split("</style>", 1)[0]
intake_js = template.split(js_marker, 1)[1].split(
    "// UX02A_POOL_INVENTORY_V1", 1
)[0]

# Dedicated local target, sem transformar o restante do Workspace em drop zone.
assert 'id="pane-context"' in pool
assert 'id="pool-intake-dropzone"' in drop_markup
assert drop_start in pool and drop_end in pool
assert 'role="region"' in drop_markup
assert 'aria-busy="false"' in drop_markup

for event_name in ("dragenter", "dragover", "dragleave", "drop"):
    listener = f".addEventListener('{event_name}'"
    assert template.count(listener) == 1
    assert f"poolIntakeDropzone?{listener}" in intake_js

for global_target in ("document", "window", "document.body"):
    for event_name in ("dragenter", "dragover", "dragleave", "drop"):
        assert (
            f"{global_target}.addEventListener('{event_name}'"
            not in template
        )

# Picker nativo preservado, unitário e ligado ao mesmo handler do drop.
input_match = re.search(
    r'<input id="document-intake-input"[^>]*>',
    pool,
)
assert input_match
assert 'type="file"' in input_match.group(0)
assert " multiple" not in input_match.group(0)
assert 'id="document-intake-trigger"' in pool
assert "documentIntakeInput?.click()" in intake_js
assert "async function incorporateDocumentFile(file)" in intake_js
assert intake_js.count("incorporateDocumentFile(files[0])") == 2
assert "documentIntakeInput.value=''" in intake_js

# Um arquivo por operação; zero é ignorado e múltiplos são rejeitados.
assert "if(files.length===0)return" in intake_js
assert "if(files.length!==1)" in intake_js
assert "exatamente um arquivo por vez" in intake_js
assert "if(documentIntakeBusy){" in intake_js

# Contrato canônico único, sem endpoint ou campo alternativo.
canonical_endpoint = (
    "/api/cases/'+encodeURIComponent(caseRef)+'/documents/intake"
)
assert template.count(canonical_endpoint) == 1
assert "const formData=new FormData()" in intake_js
assert "formData.append('file',file)" in intake_js
assert "method:'POST'" in intake_js

# Cinco resultados perceptíveis, com mínimos explícitos de apresentação.
required_states = {
    "started": "'started'",
    "working": "'working'",
    "success": "'success'",
    "duplicate": "'duplicate'",
    "error": "'error'",
}
for state, marker in required_states.items():
    assert marker in intake_js
    assert f".is-{state}" in intake_css

assert "let kind='success'" in intake_js
assert "kind='duplicate'" in intake_js
assert "'Intake iniciado'" in intake_js
assert "'Intake iniciado — Incorporando…'" in intake_js
assert "error?.message||'Não foi possível incorporar o material.'" in intake_js

started_min = re.search(
    r"const INTAKE_STARTED_MIN_MS=(\d+);",
    intake_js,
)
processing_min = re.search(
    r"const INTAKE_PROCESSING_MIN_MS=(\d+);",
    intake_js,
)
assert started_min and int(started_min.group(1)) == 600
assert processing_min and int(processing_min.group(1)) == 1000
assert "function waitForIntakePresentation(milliseconds)" in intake_js
assert "setTimeout(resolve,milliseconds)" in intake_js

progress = intake_js.split(
    "async function presentDocumentIntakeProgress(file)", 1
)[1].split("async function incorporateDocumentFile(file)", 1)[0]
started_wait = "waitForIntakePresentation(INTAKE_STARTED_MIN_MS)"
processing_wait = "waitForIntakePresentation(INTAKE_PROCESSING_MIN_MS)"
assert progress.index(started_wait) < progress.index("'working'")
assert progress.index("'working'") < progress.index(processing_wait)
processing_message = "'Intake iniciado — Incorporando…'"
assert processing_message in progress
assert "Intake iniciado" in processing_message
assert "Incorporando…" in processing_message

# O fetch começa antes de qualquer espera; a conclusão aguarda os dois fluxos.
request_flow = intake_js.split(
    "async function requestDocumentIntake(file)", 1
)[1].split("async function presentDocumentIntakeProgress(file)", 1)[0]
assert "await fetch(" in request_flow
assert "waitForIntakePresentation" not in request_flow
assert request_flow.index("await fetch(") == request_flow.index("await ")

incorporate = intake_js.split(
    "async function incorporateDocumentFile(file)", 1
)[1].split("documentIntakeInput?.addEventListener", 1)[0]
request_start = "const requestPromise=requestDocumentIntake(file);"
presentation_start = (
    "const presentationPromise=presentDocumentIntakeProgress(file);"
)
assert request_start in incorporate
assert presentation_start in incorporate
assert incorporate.index(request_start) < incorporate.index("await ")
assert incorporate.index(request_start) < incorporate.index(
    presentation_start
)
assert "await Promise.all(" in incorporate
assert "[requestPromise,presentationPromise]" in incorporate

# Não há espera ocupada; a espera perceptiva cede o event loop.
assert not re.search(r"\bwhile\s*\(", intake_js)
assert "for(;;)" not in intake_js.replace(" ", "")
assert "Atomics.wait" not in intake_js

# Concorrência bloqueada e disponibilidade restaurada em todas as saídas.
assert "let documentIntakeBusy=false" in intake_js
assert "if(!file||documentIntakeBusy)return" in intake_js
assert "if(documentIntakeBusy)" in intake_js
assert "setDocumentIntakeBusy(true)" in intake_js
assert "finally{" in intake_js
assert "setDocumentIntakeBusy(false)" in intake_js

# Created/hydrated reidratam CaseMaterials; duplicidade só informa o registro.
assert (
    "payload?.status==='created'||payload?.status==='hydrated'"
    in intake_js
)
assert "sessionStorage.setItem(" in intake_js
assert "window.location.reload()" in intake_js
assert "payload?.status==='duplicate'" in intake_js
assert "Nenhuma nova cópia foi criada." in intake_js
assert "payload?.error" in intake_js

# Recuperação governada e fronteiras do contrato congelado.
assert '/api/documents/{{ item.id }}/original' in pool
for forbidden_template in (
    "storage_relpath",
    "absolute_path",
    "LocalCaseStorage",
    "file://",
):
    assert forbidden_template.lower() not in template.lower()

for forbidden_intake in (
    "OCR",
    "Smart Bin",
    "classificação por IA",
    "dataTransfer.setData",
    'draggable="true"',
):
    assert forbidden_intake.lower() not in intake_js.lower()
    assert forbidden_intake.lower() not in drop_markup.lower()

# UX-02A permanece presente e determinística.
for marker in (
    'id="pool-inventory-search"',
    'id="pool-family-filter"',
    'id="pool-document-filter"',
    'id="pool-selection-mode-toggle"',
    "function populateDocumentTypeFilters()",
    "function applyPoolInventoryFilters()",
    "function setPoolSelectionMode(active)",
):
    assert marker in template

print("UX-02B WORKSPACE POOL INTAKE SMOKE: OK")
print("drop-scope=pool-only")
print("native-picker=preserved")
print("single-file=explicit")
print("shared-handler=yes")
print("states=started,working,success,duplicate,error")
print("presentation-minimums=started-600ms,working-1000ms")
print("canonical-intake=preserved")
print("ux02a=preserved")
