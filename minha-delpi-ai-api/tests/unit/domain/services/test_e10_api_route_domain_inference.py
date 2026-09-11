"""E10.S2 — apiRouteDomain inference without JSON pathMarkers."""

from __future__ import annotations

from app.domain.services.api_route_domain_inference_service import (
    ApiRouteDomainInferenceService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)


def test_infer_product_search_positive():
    assert ApiRouteDomainInferenceService.infer_from_path("/products/search") == (
        "product_search"
    )
    assert ChatOperationalApiDomainService.classify_path("/products/search") == (
        "product_search"
    )


def test_infer_department_kpi_vs_production_schedule_sibling():
    assert (
        ApiRouteDomainInferenceService.infer_from_path("/production/otd")
        == "department_kpi"
    )
    assert (
        ApiRouteDomainInferenceService.infer_from_path("/production/schedule/01")
        == "production_schedule"
    )


def test_infer_unknown_path_negative_generic():
    assert ApiRouteDomainInferenceService.infer_from_path("/unknown/xyz") == "generic"


def test_infer_explicit_delpi_metadata_wins():
    domain = ApiRouteDomainInferenceService.infer_from_action(
        {
            "path": "/anything",
            "delpiMetadata": {"apiRouteDomain": "product"},
        }
    )
    assert domain == "product"


def test_classify_action_uses_catalog_metadata():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {
                "path": "/products/{code}/stock",
                "delpi_metadata": {"apiRouteDomain": "product"},
            }
        )
        == "product"
    )
