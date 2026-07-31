"""Mutações do DataModelDraft (assistente de dados TV)."""

from __future__ import annotations

from tv_app.application.services.data.tv_data_builder_draft import (
    add_source,
    empty_draft,
    propose_join,
    remove_source,
    set_columns,
    set_params,
)
from tv_app.application.services.data.tv_data_builder_service import TvDataBuilderService
from tv_app.application.services.data.tv_data_builder_session_store import TvDataBuilderSessionStore


class _FakeCatalog:
    def __init__(self, routes: dict[str, dict]) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)

    def list_routes(self):
        return list(self._routes.values())


class _FakeSuggest:
    def __init__(self, suggestions: list[dict] | None = None) -> None:
        self._suggestions = suggestions or []

    def suggest(self, *, query: str, limit: int = 5) -> dict:
        return {
            "query": query,
            "suggestions": self._suggestions[:limit],
            "total": len(self._suggestions[:limit]),
            "degraded": False,
        }


def test_add_remove_source_and_status():
    draft = empty_draft()
    draft, src_a = add_source(draft, operation_id="get_otd", label="OTD")
    assert src_a is not None
    assert draft["status"] == "ready"
    assert draft["primaryLocalId"] == src_a["localId"]

    draft, again = add_source(draft, operation_id="get_otd", label="OTD")
    assert again is None
    assert len(draft["sources"]) == 1

    draft, src_b = add_source(draft, operation_id="get_pcp", label="PCP")
    assert len(draft["sources"]) == 2

    draft, removed = remove_source(draft, local_id=src_a["localId"])
    assert removed is not None
    assert draft["primaryLocalId"] == src_b["localId"]
    assert len(draft["sources"]) == 1


def test_set_params_and_columns():
    draft = empty_draft()
    draft, src = add_source(draft, operation_id="get_otd", label="OTD", params={})
    draft, updated = set_params(draft, params={"branch": "01"}, local_id=src["localId"])
    assert updated["params"]["branch"] == "01"

    draft = set_columns(draft, ["op", "days_late"])
    steps = draft["transform"]["steps"]
    assert any(s.get("op") == "select" and s.get("columns") == ["op", "days_late"] for s in steps)


def test_propose_join_merge_step():
    draft = empty_draft()
    draft, left = add_source(draft, operation_id="get_otd", label="OTD")
    draft, right = add_source(draft, operation_id="get_pcp", label="PCP")
    draft, step = propose_join(draft, left_key="op", right_key="op")
    assert step is not None
    assert step["op"] == "merge"
    assert step["sourceId"] == right["localId"]
    assert draft["primaryLocalId"] == left["localId"]
    assert draft["status"] == "ready"


def test_materialize_attaches_transform_on_primary():
    store = TvDataBuilderSessionStore()
    catalog = _FakeCatalog(
        {
            "get_otd": {"operationId": "get_otd", "label": "OTD", "parameters": []},
            "get_pcp": {"operationId": "get_pcp", "label": "PCP", "parameters": []},
        }
    )
    service = TvDataBuilderService(catalog, store=store, suggest=_FakeSuggest())
    session = service.create_session()
    sid = session["id"]

    service.turn(sid, action={"type": "add_source", "operationId": "get_otd"})
    service.turn(sid, action={"type": "add_source", "operationId": "get_pcp"})
    service.turn(sid, action={"type": "propose_join", "leftKey": "op", "rightKey": "op"})
    service.turn(sid, action={"type": "set_columns", "columns": ["op", "days_late"]})
    service.turn(sid, message="filial 01")

    result = service.materialize(sid)
    assert result["ok"] is True
    assert len(result["blocks"]) == 2
    primary = next(b for b in result["blocks"] if b.get("isPrimary"))
    assert primary["dataTransform"]["steps"]
    ops = [s.get("op") for s in primary["dataTransform"]["steps"]]
    assert "merge" in ops
    assert "select" in ops
    assert primary["dataBinding"]["params"].get("branch") == "01"


def test_turn_suggest_returns_cards():
    store = TvDataBuilderSessionStore()
    catalog = _FakeCatalog(
        {"get_pcp_items": {"operationId": "get_pcp_items", "label": "PCP items", "parameters": []}}
    )
    suggest = _FakeSuggest(
        [
            {
                "operationId": "get_pcp_items",
                "label": "PCP items",
                "reason": "ops em atraso",
                "score": 0.9,
            }
        ]
    )
    service = TvDataBuilderService(catalog, store=store, suggest=suggest)
    session = service.create_session()
    next_session = service.turn(session["id"], message="ops em atraso pcp")
    last = next_session["messages"][-1]
    assert last["role"] == "assistant"
    assert last["suggestions"][0]["operationId"] == "get_pcp_items"


def test_preview_intent_does_not_suggest():
    store = TvDataBuilderSessionStore()
    catalog = _FakeCatalog(
        {"get_otd": {"operationId": "get_otd", "label": "OTD", "parameters": []}}
    )
    service = TvDataBuilderService(
        catalog,
        store=store,
        suggest=_FakeSuggest([{"operationId": "get_otd", "label": "OTD"}]),
    )
    session = service.create_session()
    sid = session["id"]
    service.turn(sid, action={"type": "add_source", "operationId": "get_otd"})

    next_session = service.turn(sid, message="mostre uma prévia")
    assistant_tools = [
        m.get("tool")
        for m in next_session["messages"]
        if m.get("role") == "assistant"
    ]
    assert "suggest_sources" not in assistant_tools[-3:]
    assert "preview" in assistant_tools


def test_extract_preview_table_from_resolved_preview():
    selected = {
        "resolved": {
            "preview": {
                "columns": [{"key": "op"}, {"key": "days_late"}],
                "rows": [{"op": "1", "days_late": 3}],
            }
        }
    }
    table = TvDataBuilderService._extract_preview_table(selected)
    assert table["columns"] == ["op", "days_late"]
    assert table["rows"] == [["1", 3]]
    assert table["rowCount"] == 1
