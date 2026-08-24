from __future__ import annotations
from pathlib import Path


def main() -> None:
    text = Path("app/templates/workspace.html").read_text(encoding="utf-8")

    # UX-01 geometry/surface contract must remain present even after UX-02.
    required = (
        "UX01_WORKSPACE_SPATIAL_HIERARCHY_V1",
        "UX01_WORKSPACE_SPATIAL_HIERARCHY_V1_1",
        "function defaultLayout()",
        "layoutStorageKey='circe-athena.workspace.layout.v2'",
        "legacyLayoutStorageKey='circe-athena.workspace.layout.v1'",
        "layoutVersion='ux01.1'",
        "version!==layoutVersion",
        "total*.235",
        "ambient ? 0.205 : 0.225",
        "workMin:440",
        "athena-pane--ambient",
        ".work-topic-tab::after",
        ".work-topic-tab--active",
        ".work-topic-card__top>div:first-child{display:none}",
        ".athena-pane .report-topic-paper{width:min(100%,760px)",
    )
    for marker in required:
        assert marker in text, marker

    # Capabilities that UX-01 was required to preserve.
    preserved = (
        "bindSplitter(splitterContext,'context')",
        "bindSplitter(splitterAthena,'athena')",
        "collapseStorageKey='circe-athena.workspace.collapse.v1'",
        'data-detach-pane="pool"',
        'data-detach-pane="work"',
        'data-detach-pane="athena"',
        "window.__athenaWorkspaceChannel",
        "resetWorkspaceLayout?.addEventListener",
        "localPoolSelectionTokens",
        "BANDEJA DA MESA",
        "fact-row__summary",
    )
    for marker in preserved:
        assert marker in text, marker

    # Current coexistence contract: UX-02 may exist, but must not erase UX-01.
    for marker in (
        "UX02_TOPIC_OPERATIONAL_PROGRESSION_V2",
        'data-ux02-stage="sources"',
        'data-ux02-stage="map"',
        'data-ux02-stage="context"',
        'data-ux02-stage="narrative"',
        'data-ux02-stage="review"',
    ):
        assert marker in text, marker

    # STAB-01 must coexist with the same geometry.
    for marker in (
        "STAB01R_INTERACTION_CONTROLLER_V1",
        "STAB01S_RESTORE_POOL_DND_HELPERS",
        "STAB01T_TOPIC_STATUS_BUTTON_SCOPE",
    ):
        assert marker in text, marker

    print("UX-01.1 REGRESSION SMOKE: OK")
    print("geometry=preserved layout-v2=preserved panes=preserved UX02=coexists STAB01=coexists")


if __name__ == "__main__":
    main()
