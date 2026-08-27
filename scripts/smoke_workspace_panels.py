from pathlib import Path

template = Path(
    "app/templates/workspace.html"
).read_text(
    encoding="utf-8-sig"
)

required = {
    "panels-final":
        "UX01_PANELS_FINAL_V1",

    "pool-toggle":
        'id="toggle-context-pane"',

    "right-toggle":
        'id="toggle-right-pane"',

    "pool-open-glyph":
        "&#8249;",

    "right-open-glyph":
        "&#8250;",

    "pool-js-glyph":
        "String.fromCharCode(8250)",

    "right-js-glyph":
        "String.fromCharCode(8249)",

    "mesa-title":
        "CONSTRU&Ccedil;&Atilde;O DO RELAT&Oacute;RIO",

    "code-label":
        "C&Oacute;DIGO",

    "user-label":
        "USU&Aacute;RIO",

    "right-collapse":
        "right-collapsed",

    "collapse-v2":
        "circe-athena.workspace.collapse.v2",
}

forbidden = {
    "work-toggle":
        'id="toggle-work-pane"',

    "work-collapsed":
        "work-collapsed",

    "legacy-collapse":
        "AT06A_COLLAPSIBLE_PANES_V1",
}

missing = [
    name
    for name, marker in required.items()
    if marker not in template
]

leaks = [
    name
    for name, marker in forbidden.items()
    if marker in template
]

if missing or leaks:
    parts=[]

    if missing:
        parts.append(
            "missing=" + ",".join(missing)
        )

    if leaks:
        parts.append(
            "legacy=" + ",".join(leaks)
        )

    raise SystemExit(
        "UX-01 WORKSPACE PANELS SMOKE: FAIL -> "
        + " | ".join(parts)
    )

print("UX-01 WORKSPACE PANELS SMOKE: OK")
print("encoding-safe=yes")
print("mesa-collapsible=no")
print("pool-collapsible=yes")
print("right-column-collapsible=yes")
