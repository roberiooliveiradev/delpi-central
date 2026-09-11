"""Lint de shadow de pathMarkers — pós-E9.S12.C markers removidos do registry."""

from __future__ import annotations

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.operational_route_registry_lint_service import (
    OperationalRouteRegistryLintReport,
    OperationalRouteRegistryLintService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
    invalidate_operational_route_registry_cache,
)
from app.domain.services.chat_assistant_content_service import (
    invalidate_assistant_content_cache,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()
    invalidate_assistant_content_cache()
    invalidate_operational_route_registry_cache()


def test_openapi_get_paths_include_product_and_customer_search() -> None:
    paths = OperationalRouteRegistryLintService._openapi_get_paths()

    assert any(path.endswith("/products/search") or path == "/products/search" for path in paths)
    assert any("/customers/search" in path for path in paths)


def test_product_search_routes_have_no_path_marker_shadow() -> None:
    report = OperationalRouteRegistryLintReport()
    OperationalRouteRegistryLintService._lint_path_marker_shadow(report)

    assert report.ok, report.errors


def test_product_search_by_description_keeps_observer_operation_ids() -> None:
    route = OperationalRouteRegistryService.route_by_id("productSearchByDescription")
    assert route is not None
    route_spec = route.get("route") or {}

    # E11.S5 — arrays may remain as observer; not routing authority.
    assert "search_products" in (route_spec.get("operationIds") or [])
    assert not (route_spec.get("pathMarkers") or [])
    assert not (route_spec.get("pathSuffix") or "")

    from pathlib import Path
    import json

    payload = json.loads(
        (
            Path(__file__).resolve().parents[4]
            / "app/content/pt-BR/assistant/operational_route_registry.json"
        ).read_text(encoding="utf-8")
    )
    assert payload.get("cleanupMeta", {}).get("operationIdsRuntimeAuthority") is False
    assert payload.get("cleanupMeta", {}).get("operationIdsRole") == "observer"
