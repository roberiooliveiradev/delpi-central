"""Intersect allowlist TV com candidatos do chat base (dry-run)."""

from __future__ import annotations

import httpx

from tv_app.application.services.data.tv_data_route_suggest_service import (
    TvDataRouteSuggestService,
)


class _FakeCatalog:
    def __init__(self, routes: dict[str, dict]) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


class _FakeAi:
    def __init__(self, payload: dict | None = None, *, error: Exception | None = None) -> None:
        self._payload = payload or {"suggestions": []}
        self._error = error
        self.calls: list[dict] = []

    def suggest_operational_routes(self, *, query: str, limit: int = 5) -> dict:
        self.calls.append({"query": query, "limit": limit})
        if self._error is not None:
            raise self._error
        return self._payload


def test_suggest_intersects_catalog_and_preserves_rank():
    catalog = _FakeCatalog(
        {
            "get_oee_tv": {
                "operationId": "get_oee_tv",
                "label": "OEE TV",
                "category": "production",
            },
            "get_stock_tv": {
                "operationId": "get_stock_tv",
                "label": "Estoque TV",
                "category": "supplies",
            },
        }
    )
    ai = _FakeAi(
        {
            "suggestions": [
                {
                    "operationId": "chat_only_route",
                    "reason": "só no chat",
                    "score": 0.99,
                    "domain": "product",
                },
                {
                    "operationId": "get_oee_tv",
                    "reason": "eficiência fabril",
                    "score": 0.9,
                    "domain": "production",
                },
                {
                    "operationId": "get_stock_tv",
                    "reason": "estoque",
                    "score": 0.7,
                    "domain": "supplies",
                },
            ]
        }
    )
    result = TvDataRouteSuggestService(catalog, ai_client=ai).suggest(
        query="oee da semana",
        limit=5,
    )
    assert result["degraded"] is False
    assert result["query"] == "oee da semana"
    ids = [row["operationId"] for row in result["suggestions"]]
    assert ids == ["get_oee_tv", "get_stock_tv"]
    assert "chat_only_route" not in ids
    assert result["suggestions"][0]["reason"] == "eficiência fabril"
    assert result["suggestions"][0]["label"] == "OEE TV"


def test_suggest_respects_limit_after_intersect():
    catalog = _FakeCatalog(
        {
            f"route_{i}": {"operationId": f"route_{i}", "label": f"R{i}"}
            for i in range(5)
        }
    )
    ai = _FakeAi(
        {
            "suggestions": [
                {"operationId": f"route_{i}", "reason": f"r{i}", "score": 1.0 - i * 0.1}
                for i in range(5)
            ]
        }
    )
    result = TvDataRouteSuggestService(catalog, ai_client=ai).suggest(query="lista completa", limit=2)
    assert result["total"] == 2
    assert [row["operationId"] for row in result["suggestions"]] == ["route_0", "route_1"]


def test_suggest_degraded_when_ai_unavailable():
    catalog = _FakeCatalog({"get_oee_tv": {"operationId": "get_oee_tv", "label": "OEE"}})
    ai = _FakeAi(error=httpx.ConnectError("down"))
    result = TvDataRouteSuggestService(catalog, ai_client=ai).suggest(query="oee", limit=3)
    assert result["degraded"] is True
    assert result["suggestions"] == []
    assert result["error"] == "ai_unavailable"


def test_suggest_empty_query():
    catalog = _FakeCatalog({})
    ai = _FakeAi({"suggestions": [{"operationId": "x"}]})
    result = TvDataRouteSuggestService(catalog, ai_client=ai).suggest(query="  ", limit=3)
    assert result["suggestions"] == []
    assert ai.calls == []
