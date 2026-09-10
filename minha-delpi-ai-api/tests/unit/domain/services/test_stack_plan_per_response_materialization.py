"""E3 — materialização per-response no stackPresentationPlan."""

from __future__ import annotations

from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


def test_materialize_display_titles_only_current_route(monkeypatch):
    plan: dict = {
        "presentationProfileKey": "product_stock",
        "narrativeOrder": ["lead", "highlights", "operationalTables"],
        "tableRoleOrder": ["stock"],
    }
    metadata = {
        "path": "/products/10080001/stock",
        "summary": "Consultar estoque do produto por filial",
        "actionId": "get_product_stock",
    }

    ChatPresentationStackOrderService._materialize_display_titles(metadata, plan)

    assert plan.get("resolvedRouteTitle")
    assert "estoque" in str(plan.get("resolvedRouteTitle") or "").casefold()
    route_titles = plan.get("routeTitles") or {}
    assert isinstance(route_titles, dict)
    assert len(route_titles) == 1
    assert "stock" in route_titles
    route_framing = plan.get("routeFraming") or {}
    assert isinstance(route_framing, dict)
    assert len(route_framing) <= 1
    # Não deve dumpar o catálogo inteiro (stock/structure/inspection/…)
    assert set(route_titles.keys()).issubset({"stock", "other", "product_stock"})


def test_materialize_unknown_route_without_catalog_dependency(monkeypatch):
    plan: dict = {
        "presentationProfileKey": "unknown_widget_inventory",
        "narrativeOrder": ["lead", "operationalTables"],
    }
    metadata = {
        "path": "/acme/widgets/inventory",
        "summary": "Consultar inventário de widgets",
        "actionId": "acme.widgets.inventory",
        "providerKey": "acme-erp",
    }

    ChatPresentationStackOrderService._materialize_display_titles(metadata, plan)

    assert plan.get("resolvedRouteTitle")
    assert "inventário" in str(plan.get("resolvedRouteTitle") or "").casefold()
    assert len(plan.get("routeTitles") or {}) == 1
