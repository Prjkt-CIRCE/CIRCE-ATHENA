from pathlib import Path

template = Path("app/templates/workspace.html").read_text(
    encoding="utf-8-sig"
)

required = {
    "ux01-base": "UX01_SHELL_V1",
    "ux01-refinement": "UX01_SHELL_REFINEMENT_V2",
    "brand": "CIRCE-ATHENA",
    "codigo": "C?DIGO",
    "status": "STATUS",
    "usuario": "USU?RIO",
    "pool": ">Pool<",
    "mesa": ">Mesa<",
    "right-column": 'id="pane-right"',
    "inspector": 'id="workspace-inspector"',
    "composer": "ATHENA // COMPOSER",
    "mock-ratio": "layoutRatios={context:.27,athena:.31}",
    "layout-v3": "circe-athena.workspace.layout.v3",
    "canonical-intake":
        "/api/cases/'+encodeURIComponent(caseRef)+'/documents/intake",
    "governed-original":
        '/api/documents/{{ item.id }}/original',
    "block-form": 'id="create-block-form"',
    "assistant-query": "/api/assistant/query",
}

forbidden = {
    "legacy-sidebar":
        '{% include "partials/sidebar.html" %}',
}

missing = [
    name for name, marker in required.items()
    if marker not in template
]

leaks = [
    name for name, marker in forbidden.items()
    if marker in template
]

if missing or leaks:
    details = []
    if missing:
        details.append("missing=" + ",".join(missing))
    if leaks:
        details.append("legacy=" + ",".join(leaks))

    raise SystemExit(
        "UX-01 WORKSPACE SHELL SMOKE: FAIL -> "
        + " | ".join(details)
    )

print("UX-01 WORKSPACE SHELL SMOKE: OK")
print("immersive-workspace=yes")
print("legacy-sidebar=no")
print("mock-ratio=27/42/31")
print("canonical-intake=preserved")
print("assistant-query=preserved")
