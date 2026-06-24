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
        entity="pac_inspection_lot",
        shape="paged_list",
    )

    assert profile["openapiDerived"] is True
    assert profile["openapiEntity"] == "pac_inspection_lot"
    assert profile["openapiShape"] == "paged_list"
    assert profile["presentationStrategy"] == "as_delivered"
    assert profile["defaultViewPolicy"] == "table_when_available"
    assert profile["profileKey"] == "openapi:pac_inspection_lot"


def test_resolve_profile_uses_openapi_derived_for_unmapped_entity():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/api-pac-quality/v1/lots",
        entity="pac_inspection_lot",
        shape="paged_list",
    )

    assert profile.get("openapiDerived") is True
    assert profile["profileKey"] == "openapi:pac_inspection_lot"


def test_resolve_profile_keeps_json_entity_profile_mapping():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/products/90269001/stock",
        entity="product_stock",
        shape="paged_list",
    )

    assert profile.get("openapiDerived") is not True
    assert profile["profileKey"] == "stock"


def test_cache_presentation_profile_on_metadata():
    metadata = {
        "path": "/api-pac-quality/v1/lots",
        "apiDelpiResponseMeta": {
            "entity": "pac_inspection_lot",
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
