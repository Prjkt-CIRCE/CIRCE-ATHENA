"""CURATED-01B smoke: Workspace route consumes canonical case materials."""

from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace

import app.routes.workspace as route


class FakeQuery:
    def __init__(self, workspace):
        self.workspace = workspace

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.workspace


class FakeDB:
    def __init__(self, workspace):
        self.workspace = workspace
        self.closed = False

    def query(self, model):
        return FakeQuery(self.workspace)

    def close(self):
        self.closed = True


class FakeTemplates:
    def TemplateResponse(self, name, context):
        return SimpleNamespace(template=name, context=context)


class FakeRequest:
    session = {"operator": {"id": 7, "username": "smoke"}}


def main() -> None:
    case = SimpleNamespace(id=11, case_ref="CURATED-01B")
    person = SimpleNamespace(id=1)
    document = SimpleNamespace(id=2)
    link = SimpleNamespace(id=3)
    annotation = SimpleNamespace(id=4)
    materials = SimpleNamespace(
        case=case,
        persons=(person,),
        documents=(document,),
        links=(link,),
        annotations=(annotation,),
    )
    workspace = SimpleNamespace(id=21, shared_case_id=case.id)

    fake_db = FakeDB(workspace)
    calls = []

    original_session_local = route.SessionLocal
    original_loader = route.load_case_materials
    original_list_blocks = route.list_blocks
    original_templates = route.templates

    try:
        route.SessionLocal = lambda: fake_db
        route.load_case_materials = lambda db, *, case_ref: (
            calls.append((db, case_ref)) or materials
        )
        route.list_blocks = lambda db, workspace_id: []
        route.templates = FakeTemplates()

        response = asyncio.run(
            route.workspace_detail(FakeRequest(), "CURATED-01B", block=None)
        )

        assert calls == [(fake_db, "CURATED-01B")]
        assert fake_db.closed is True
        assert response.template == "workspace.html"

        context = response.context
        assert context["case"] is case
        assert context["workspace"] is workspace
        assert context["persons"] == [person]
        assert context["documents"] == [document]
        assert context["links"] == [link]
        assert context["annotations"] == [annotation]
        assert context["blocks"] == []
        assert context["active_block"] is None

    finally:
        route.SessionLocal = original_session_local
        route.load_case_materials = original_loader
        route.list_blocks = original_list_blocks
        route.templates = original_templates

    source = inspect.getsource(route.workspace_detail)
    assert "load_case_materials(" in source
    assert "list(case.persons)" not in source
    assert "list(case.documents)" not in source
    assert "list(case.links)" not in source
    assert "list(case.annotations)" not in source

    print("CURATED-01B WORKSPACE MATERIAL INTEGRATION SMOKE: OK")
    print("canonical-loader=used")
    print("template-contract=preserved")
    print("ui-change=none")
    print("direct-relationship-read=removed")


if __name__ == "__main__":
    main()
