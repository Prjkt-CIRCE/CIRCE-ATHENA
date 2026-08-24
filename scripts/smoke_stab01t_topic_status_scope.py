from __future__ import annotations
from pathlib import Path


def main() -> None:
    text = Path("app/templates/workspace.html").read_text(encoding="utf-8")

    for marker in (
        "STAB01R_INTERACTION_CONTROLLER_V1",
        "STAB01S_RESTORE_POOL_DND_HELPERS",
        "STAB01T_TOPIC_STATUS_BUTTON_SCOPE",
        "UX02_TOPIC_OPERATIONAL_PROGRESSION_V2",
        'id="facts-workbench"',
        'data-topic-status="{{ active_topic.status }}"',
    ):
        assert marker in text, marker

    # Root cause: the generic selector attached the topic-status navigation
    # handler to #facts-workbench because the section also owns
    # data-topic-status for UX state.
    assert "document.querySelectorAll('[data-topic-status]')" not in text
    assert "document.querySelectorAll('button[data-topic-status]')" in text

    # The container state attribute MUST remain because UX-02 reads it.
    assert "ux02Workbench?.dataset.topicStatus==='completed'" in text

    # Actual topic-status controls remain buttons and keep the behavior.
    assert 'data-topic-status="in_progress" type="button"' in text
    assert "body:JSON.stringify({status:button.dataset.topicStatus})" in text
    assert "window.location.href='/workspace/'" in text

    # Previous runtime/stabilization fixes remain.
    assert "createBlockForm?.addEventListener('submit'" in text
    assert "function updateCreateDropStatus()" in text
    assert "function setSourceChecked(token,checked=true)" in text
    assert "function ux02VisibleStage()" in text

    assert "UX03" not in text
    assert "UX-03" not in text

    print("STAB-01T SMOKE: OK")
    print("topic-status-listener=buttons-only facts-workbench-state=preserved")
    print("expected-effect=click-inside-workbench-no-topic-navigation")


if __name__ == "__main__":
    main()
