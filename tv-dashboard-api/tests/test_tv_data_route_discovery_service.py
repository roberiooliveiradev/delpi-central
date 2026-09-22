"""Owner-local TV route discovery (no Chat AI)."""

from __future__ import annotations

from tv_app.application.services.data.tv_data_route_discovery_service import (
    TvDataRouteDiscoveryService,
)
from tv_app.application.services.data.tv_data_route_suggest_service import (
    TvDataRouteSuggestService,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


class _FakeCatalog:
    def __init__(self, routes: list[dict]) -> None:
        self._routes = routes

    def list_routes(self):
        return list(self._routes)

    def get_route(self, operation_id: str):
        for row in self._routes:
            if row.get("operationId") == operation_id:
                return row
        return None


def test_discover_otd_comercial_prefers_sales_order_otd():
    catalog = _FakeCatalog(
        [
            {
                "operationId": "get_supplies_purchase_order_otd",
                "path": "/supplies/purchase-order-otd",
                "label": "OTD pedidos de compra",
                "category": "supplies",
                "description": "OTD de suprimentos",
            },
            {
                "operationId": "get_sales_order_otd",
                "path": "/commercial/sales-order-otd",
                "label": "OTD de pedidos de venda",
                "category": "commercial",
                "description": "OTD comercial",
            },
            {
                "operationId": "get_sales_order_otd_series",
                "path": "/commercial/sales-order-otd/series",
                "label": "Série temporal de OTD de pedidos",
                "category": "commercial",
                "paramSchema": {
                    "granularity": {"enum": ["day", "week", "month", "year"]}
                },
            },
        ]
    )
    result = TvDataRouteDiscoveryService(catalog).discover(
        query="rota de otd comercial",
        limit=5,
    )
    ids = [row["operationId"] for row in result["suggestions"]]
    assert ids, "expected hits"
    assert ids[0].startswith("get_sales_order_otd")
    assert "get_supplies_purchase_order_otd" not in ids[:2]
    assert result["searchMissDoesNotProveAbsence"] is True


def test_discover_otd_suprimentos_sibling():
    catalog = _FakeCatalog(
        [
            {
                "operationId": "get_sales_order_otd",
                "path": "/commercial/sales-order-otd",
                "label": "OTD pedidos venda",
                "category": "commercial",
            },
            {
                "operationId": "get_supplies_purchase_order_otd",
                "path": "/supplies/purchase-order-otd",
                "label": "OTD pedidos compra",
                "category": "supplies",
            },
        ]
    )
    result = TvDataRouteDiscoveryService(catalog).discover(
        query="otd suprimentos",
        limit=3,
    )
    ids = [row["operationId"] for row in result["suggestions"]]
    assert ids[0] == "get_supplies_purchase_order_otd"


def test_discover_empty_query_negative():
    catalog = _FakeCatalog(
        [{"operationId": "get_sales_order_otd", "path": "/commercial/sales-order-otd"}]
    )
    result = TvDataRouteDiscoveryService(catalog).discover(query="  ", limit=5)
    assert result["suggestions"] == []
    assert result["total"] == 0


def test_suggest_facade_uses_discovery_not_ai():
    catalog = TvDataRouteCatalogService()
    result = TvDataRouteSuggestService(catalog).suggest(
        query="otd comercial",
        limit=5,
    )
    assert result["degraded"] is False
    ids = [row["operationId"] for row in result["suggestions"]]
    assert any("sales_order_otd" in oid for oid in ids)
    assert not any(
        "supplies" in str(row.get("path") or "") for row in result["suggestions"][:2]
    )


def test_live_catalog_series_exposes_week_granularity():
    catalog = TvDataRouteCatalogService()
    route = catalog.get_route("get_sales_order_otd_series")
    assert route is not None
    schema = route.get("paramSchema") or {}
    granularity = schema.get("granularity") or {}
    assert "week" in (granularity.get("enum") or [])
