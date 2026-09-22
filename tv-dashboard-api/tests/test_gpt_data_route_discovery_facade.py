"""GPT façade: owner-local data route search + preview shortcut."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def _user():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")


def _dispatch() -> GptActionsDispatchService:
    repo = MagicMock()
    writes = MagicMock()
    commit = MagicMock()
    return GptActionsDispatchService(repo=repo, writes=writes, commit=commit)


def test_search_requires_query():
    dispatch = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        dispatch.search_data_routes(user=_user(), query="  ", limit=8)
    assert exc.value.code == "QUERY_REQUIRED"
    assert exc.value.status_code == 422


def test_search_otd_comercial_returns_compact_dto_with_param_schema():
    dispatch = _dispatch()
    result = dispatch.search_data_routes(user=_user(), query="otd comercial", limit=8)
    assert result["searchMissDoesNotProveAbsence"] is True
    assert result["query"] == "otd comercial"
    assert result["items"], "expected catalog hits"
    assert all(
        "sales-order-otd" in str(item.get("path") or "")
        or "sales_order_otd" in str(item.get("operationId") or "")
        for item in result["items"]
    )
    assert result["items"][0].get("category") == "commercial"
    series = next(
        (
            item
            for item in result["items"]
            if item.get("operationId") == "get_sales_order_otd_series"
        ),
        None,
    )
    assert series is not None
    schema = series.get("paramSchema") or {}
    gran = schema.get("granularity") or {}
    assert "week" in (gran.get("enum") or [])
    # Compact: no encyclopedia fields dumped wholesale
    assert "sql" not in series
    assert "openapi" not in series


def test_search_does_not_dump_full_catalog_without_intent():
    dispatch = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        dispatch.search_data_routes(user=_user(), query=None, limit=50)
    assert exc.value.code == "QUERY_REQUIRED"
    catalog_size = len(TvDataRouteCatalogService().list_routes())
    assert catalog_size > 20


def test_openapi_search_query_required_and_preview_shortcut():
    doc = build_gpt_actions_openapi(server_url="https://example.com/apps/tv-dashboard-api")
    search = None
    preview = None
    for methods in doc["paths"].values():
        get = methods.get("get") if isinstance(methods, dict) else None
        post = methods.get("post") if isinstance(methods, dict) else None
        if isinstance(get, dict) and get.get("operationId") == "gpt_search_data_routes":
            search = get
        if isinstance(post, dict) and post.get("operationId") == "gpt_preview_data_block":
            preview = post
    assert search is not None and preview is not None
    params = {p["name"]: p for p in search["parameters"]}
    assert params["query"]["required"] is True
    assert params["limit"]["schema"]["default"] == 8
    assert params["limit"]["schema"]["maximum"] == 20
    assert "category" in params
    assert "dump" in search["description"].lower() or "never dump" in search["description"].lower()
    schema = preview["requestBody"]["content"]["application/json"]["schema"]
    assert "required" not in schema or "block" not in schema.get("required", [])
    assert "operationId" in schema["properties"]
    assert "params" in schema["properties"]


def test_preview_operation_id_params_builds_block(monkeypatch):
    dispatch = _dispatch()
    captured: dict = {}

    def _fake_preview(block, **kwargs):
        captured["block"] = block
        captured["native"] = kwargs.get("native_config")
        return {"id": block.get("id"), "resolved": {"ok": True}}

    monkeypatch.setattr(dispatch._preview, "preview_block", _fake_preview)
    monkeypatch.setattr(dispatch._validation, "sanitize", lambda cfg: cfg)

    result = dispatch.preview_data_block(
        user=_user(),
        body={
            "operationId": "get_sales_order_otd_series",
            "params": {"granularity": "week"},
        },
        authorization=None,
    )
    assert result["persisted"] is False
    assert result["operationId"] == "get_sales_order_otd_series"
    binding = captured["block"]["dataBinding"]
    assert binding["operationId"] == "get_sales_order_otd_series"
    assert binding["params"]["granularity"] == "week"


def test_preview_param_invalid_negative():
    dispatch = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        dispatch.preview_data_block(
            user=_user(),
            body={
                "operationId": "get_sales_order_otd_series",
                "params": {"granularity": "fortnight"},
            },
            authorization=None,
        )
    assert exc.value.code == "PARAM_INVALID"


def test_preview_unknown_operation_negative():
    dispatch = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        dispatch.preview_data_block(
            user=_user(),
            body={"operationId": "get_totally_fake_route", "params": {}},
            authorization=None,
        )
    assert exc.value.code == "UNKNOWN_OPERATION"


def test_preview_legacy_block_sibling(monkeypatch):
    dispatch = _dispatch()

    def _fake_preview(block, **kwargs):
        return {"id": block.get("id"), "legacy": True}

    monkeypatch.setattr(dispatch._preview, "preview_block", _fake_preview)
    monkeypatch.setattr(dispatch._validation, "sanitize", lambda cfg: cfg)

    result = dispatch.preview_data_block(
        user=_user(),
        body={
            "block": {"id": "blk-1", "type": "kpi", "title": "L"},
            "nativeConfig": {"version": 1, "blocks": []},
        },
        authorization=None,
    )
    assert result["block"]["legacy"] is True
    assert result["operationId"] is None
