"""Lint de shadow de pathMarkers em catch-alls domainProductSearch."""

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


def test_product_search_by_description_uses_products_search_suffix() -> None:
    route = OperationalRouteRegistryService.route_by_id("productSearchByDescription")
    route_spec = route.get("route") or {}

    assert "/products/" in (route_spec.get("pathMarkers") or [])
    assert str(route_spec.get("pathSuffix") or "") == "/search"
    assert "/customers/" in (route_spec.get("excludePathMarkers") or [])
