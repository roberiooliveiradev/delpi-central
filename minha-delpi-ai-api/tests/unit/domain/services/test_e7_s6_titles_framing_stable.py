"""E7.S6 — títulos materializados estáveis (history/F5 sem reinferência)."""

from __future__ import annotations

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)
from app.domain.services.result_presentation_title_resolver import (
    SOURCE_ACTION_DISPLAY_LABEL,
    SOURCE_PRESENTATION_TITLE,
    ResultPresentationTitleResolver,
)

configure_domain_infrastructure_ports()


def test_e7_s6_rematerialize_preserves_stable_title():
    """Positive: segundo resolve_plan (F5) não troca título com titleSource estável."""

    metadata = {
        "path": "/products/10080001/stock",
        "summary": "Consultar estoque do produto por filial",
        "actionId": "get_product_stock",
    }
    plan1 = ChatPresentationStackOrderService.resolve_plan(metadata)
    title1 = str(plan1.get("resolvedRouteTitle") or "")
    source1 = str(metadata.get("titleSource") or plan1.get("titleSource") or "")
    assert title1
    assert source1

    # Simula persistência + rematerialize (history/F5) com path potencialmente diferente.
    reloaded = {
        "path": "/products/10080001/stock-renamed",
        "summary": metadata["summary"],
        "actionId": metadata["actionId"],
        "title": title1,
        "routeTitle": title1,
        "titleSource": (
            source1
            if source1
            in {
                SOURCE_ACTION_DISPLAY_LABEL,
                SOURCE_PRESENTATION_TITLE,
            }
            else SOURCE_PRESENTATION_TITLE
        ),
        "presentation": {"title": title1},
    }
    plan2 = ChatPresentationStackOrderService.resolve_plan(reloaded)
    assert plan2.get("resolvedRouteTitle") == title1
    assert plan2.get("titleSource") in {
        SOURCE_PRESENTATION_TITLE,
        SOURCE_ACTION_DISPLAY_LABEL,
    }


def test_e7_s6_path_rename_keeps_materialized_title():
    """Sibling: path muda no reload; título materializado permanece."""

    metadata = {
        "path": "/legacy/stock-view",
        "title": "Estoque por filial",
        "routeTitle": "Estoque por filial",
        "titleSource": SOURCE_PRESENTATION_TITLE,
        "summary": "Consultar estoque do produto por filial",
        "actionId": "get_product_stock",
        "presentation": {"title": "Estoque por filial"},
    }
    plan = ChatPresentationStackOrderService.resolve_plan(
        {
            **metadata,
            "path": "/v2/products/{code}/inventory-balance",
        }
    )
    assert plan.get("resolvedRouteTitle") == "Estoque por filial"
    assert plan.get("titleSource") == SOURCE_PRESENTATION_TITLE


def test_e7_s6_negative_empty_metadata_resolves_once_from_summary():
    """Negative: sem título materializado, resolve via summary/action (não inventa LLM)."""

    resolved = ResultPresentationTitleResolver.resolve(
        path="/acme/widgets/inventory",
        summary="Consultar inventário de widgets",
        action_id="acme.widgets.inventory",
        fallback="Resultado",
    )
    assert resolved.source == SOURCE_ACTION_DISPLAY_LABEL
    assert "inventário" in resolved.title.casefold()

    plan = ChatPresentationStackOrderService.resolve_plan(
        {
            "path": "/acme/widgets/inventory",
            "summary": "Consultar inventário de widgets",
            "actionId": "acme.widgets.inventory",
        }
    )
    assert plan.get("resolvedRouteTitle")
    assert "inventário" in str(plan.get("resolvedRouteTitle") or "").casefold()
    assert plan.get("titleSource") == SOURCE_ACTION_DISPLAY_LABEL


def test_e7_s6_framing_does_not_override_title():
    """Framing contextual (routeFraming) não sobrescreve título estável."""

    metadata = {
        "path": "/products/10080001/stock",
        "title": "Título estável da action",
        "routeTitle": "Título estável da action",
        "titleSource": SOURCE_ACTION_DISPLAY_LABEL,
        "summary": "Consultar estoque do produto por filial",
        "actionId": "get_product_stock",
    }
    plan = ChatPresentationStackOrderService.resolve_plan(metadata)
    assert plan.get("resolvedRouteTitle") == "Título estável da action"
    # Framing pode existir, mas é campo separado
    framing = plan.get("routeFraming")
    if isinstance(framing, dict) and framing:
        assert "Título estável da action" not in framing.values()
