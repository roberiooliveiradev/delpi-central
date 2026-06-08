from app.domain.services.chat_api_delpi_response_profile_service import (
    CHAT_CRITICAL_ENTITIES,
    ChatApiDelpiResponseProfileService,
)


def test_resolve_prefers_meta_entity_over_path() -> None:
    profile = ChatApiDelpiResponseProfileService.resolve(
        {
            "success": True,
            "data": {"items": []},
            "meta": {
                "entity": "product_stock",
                "shape": "paged_list",
                "operationId": "get_product_stock",
            },
        },
        path="/products/90269001/analyser",
    )

    assert profile.entity == "product_stock"
    assert profile.routed_by == "meta.entity"
    assert profile.shape == "paged_list"


def test_resolve_falls_back_to_path_when_meta_missing() -> None:
    profile = ChatApiDelpiResponseProfileService.resolve(
        {"success": True, "data": {"root": {}, "items": []}},
        path="/products/90269001/structure",
    )

    assert profile.entity == "product_structure"
    assert profile.routed_by == "path"


def test_profile_coverage_meets_80_percent_threshold() -> None:
    ratio = ChatApiDelpiResponseProfileService.profile_coverage_ratio()

    assert ratio >= 0.8
    assert len(CHAT_CRITICAL_ENTITIES) >= 20


def test_enrich_humanized_appends_meta_fields_glossary() -> None:
    enriched = ChatApiDelpiResponseProfileService.enrich_humanized(
        {"titulo": "Estoque", "linhas": ["2 filiais"]},
        {
            "meta": {
                "fields": {
                    "available_quantity": "Saldo disponível (atual - empenhado - reservado)",
                }
            }
        },
    )

    assert enriched is not None
    assert "available_quantity" in "\n".join(enriched.get("linhas_detalhe") or [])
