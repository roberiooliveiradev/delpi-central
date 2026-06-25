from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()


def test_build_profile_from_entity_and_shape():
    profile = OpenApiPresentationProfileDeriverService.build_profile(
        entity="quality_action_plan",
        shape="paged_list",
    )

    assert profile["openapiDerived"] is True
    assert profile["openapiEntity"] == "quality_action_plan"
    assert profile["openapiShape"] == "paged_list"
    assert profile["presentationStrategy"] == "as_delivered"
    assert profile["defaultViewPolicy"] == "table_when_available"
    assert profile["profileKey"] == "openapi:quality_action_plan"


def test_build_profile_enriched_merges_json_entity_profile():
    profile = OpenApiPresentationProfileDeriverService.build_profile(
        entity="product_analyser",
        shape="composite_analysis",
        delpi_metadata={
            "entity": "product_analyser",
            "shape": "composite_analysis",
            "presentation": {"strategy": "enriched"},
        },
    )

    assert profile["openapiPresentationStrategy"] == "enriched"
    assert profile["profileKey"] == "analyser"
    assert profile.get("stackLayoutPolicy") == "always"


def test_resolve_profile_uses_openapi_derived_for_unmapped_entity():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/quality/action-plans",
        entity="quality_action_plan",
        shape="paged_list",
    )

    assert profile.get("openapiDerived") is True
    assert profile["profileKey"] == "openapi:quality_action_plan"


def test_resolve_profile_prefers_openapi_for_replaceable_kpi_entity():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/supplies/cpv",
        entity="supplies_cpv",
        shape="scalar",
    )

    assert profile.get("openapiDerived") is True
    assert profile["profileKey"] == "openapi:supplies_cpv"
    assert profile.get("commentaryProfileKey") == "generic_kpi_series"


def test_resolve_profile_keeps_special_json_profile_when_shape_present():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/products/90269001/stock",
        entity="product_stock",
        shape="paged_list",
    )

    assert profile.get("openapiDerived") is not True
    assert profile["profileKey"] == "stock"


def test_resolve_profile_stamps_enriched_from_delpi_metadata():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/products/90269001/analyser",
        entity="product_analyser",
        shape="composite_analysis",
        delpi_metadata={
            "entity": "product_analyser",
            "shape": "composite_analysis",
            "presentation": {"strategy": "enriched"},
        },
    )

    assert profile["profileKey"] == "analyser"
    assert profile.get("openapiPresentationStrategy") == "enriched"
    assert ChatPresentationProfileService.allows_automatic_rich_stack(
        path="/products/90269001/analyser",
        entity="product_analyser",
        delpi_metadata={
            "presentation": {"strategy": "enriched"},
        },
    )


def test_cache_presentation_profile_on_metadata():
    metadata = {
        "path": "/quality/action-plans/abc",
        "apiDelpiResponseMeta": {
            "entity": "quality_action_plan",
            "shape": "paged_list",
        },
    }

    ChatPresentationProfileService.cache_presentation_profile(metadata)

    cached = metadata["presentationProfile"]

    assert cached["openapiDerived"] is True
    assert ChatPresentationProfileService.resolve_profile(
        metadata["path"],
        metadata=metadata,
    )["profileKey"] == cached["profileKey"]
