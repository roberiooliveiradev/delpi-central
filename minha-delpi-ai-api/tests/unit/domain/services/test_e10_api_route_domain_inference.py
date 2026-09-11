"""E11.S2 — apiRouteDomain from semantic metadata; path is not authority."""

from __future__ import annotations

from app.domain.services.api_route_domain_inference_service import (
    ApiRouteDomainInferenceService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)


def test_explicit_delpi_metadata_wins_over_entity_and_category():
    domain = ApiRouteDomainInferenceService.infer_from_action(
        {
            "delpiMetadata": {
                "apiRouteDomain": "product",
                "entity": "product_search",
                "category": "commercial",
            }
        },
        known_domain_ids=ChatOperationalApiDomainService.known_domain_ids(),
        category_to_domain=ChatOperationalApiDomainService.category_to_domain(),
    )
    assert domain == "product"


def test_entity_exact_product_search_positive():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {"delpi_metadata": {"entity": "product_search", "category": "products"}}
        )
        == "product_search"
    )


def test_entity_prefix_product_stock_sibling():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {"delpiMetadata": {"entity": "product_stock", "category": "products"}}
        )
        == "product"
    )


def test_category_department_kpi_when_entity_unknown():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {
                "delpiMetadata": {
                    "entity": "dashboard_si_indicator_realized",
                    "category": "commercial",
                }
            }
        )
        == "department_kpi"
    )


def test_production_schedule_entity_beats_production_category():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {
                "delpiMetadata": {
                    "entity": "production_schedule",
                    "category": "production",
                }
            }
        )
        == "production_schedule"
    )


def test_path_alone_is_generic_negative():
    assert ApiRouteDomainInferenceService.infer_from_path("/products/search") == "generic"
    assert ChatOperationalApiDomainService.classify_path("/products/search") == "generic"
    assert (
        ChatOperationalApiDomainService.classify_action(
            {"path": "/products/search", "operationId": "search_products"}
        )
        == "generic"
    )


def test_unknown_external_openapi_without_x_delpi_is_generic():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {
                "path": "/v1/widgets/{id}",
                "operationId": "getWidget",
                "tags": ["Widgets"],
            }
        )
        == "generic"
    )


def test_metamorphic_path_rename_preserves_entity_domain():
    before = ChatOperationalApiDomainService.classify_action(
        {
            "path": "/products/{code}/stock",
            "delpiMetadata": {"entity": "product_stock", "category": "products"},
        }
    )
    after = ChatOperationalApiDomainService.classify_action(
        {
            "path": "/catalog/items/{sku}/inventory",
            "delpiMetadata": {"entity": "product_stock", "category": "products"},
        }
    )
    assert before == after == "product"
