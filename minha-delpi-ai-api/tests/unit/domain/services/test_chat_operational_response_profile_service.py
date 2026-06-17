from app.domain.services.chat_operational_response_profile_service import (
    CHAT_CRITICAL_ENTITIES,
    ChatOperationalResponseProfileService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_resolve_prefers_meta_entity_over_path() -> None:
    profile = ChatOperationalResponseProfileService.resolve(
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
    profile = ChatOperationalResponseProfileService.resolve(
        {"success": True, "data": {"root": {}, "items": []}},
        path="/products/90269001/structure",
    )

    assert profile.entity == "product_structure"
    assert profile.routed_by == "path"


def test_resolve_entity_path_hint_for_kpi_route() -> None:
    profile = ChatOperationalResponseProfileService.resolve(
        {"success": True, "data": {}},
        path="/supplies/cpv",
    )

    assert profile.entity == "supplies_cpv"
    assert profile.routed_by == "path"


def test_profile_coverage_covers_all_chat_critical_entities() -> None:
    ratio = ChatOperationalResponseProfileService.profile_coverage_ratio()

    assert ratio == 1.0
    assert len(CHAT_CRITICAL_ENTITIES) >= 20


def test_entity_path_hint_for_kpi_without_http_path() -> None:
    hint = ChatOperationalResponseProfileService.entity_path_hint("supplies_cpv")

    assert hint == "/supplies/cpv"
    assert ChatOperationalResponseProfileService.presentation_path(
        path="",
        entity="supplies_cpv",
    ) == "/supplies/cpv"


def test_class_exposes_presenter_entity_constants() -> None:
    assert ChatOperationalResponseProfileService.PRODUCT_LIST_PRESENT_ENTITIES
    assert (
        "product_open_orders"
        in ChatOperationalResponseProfileService.PRODUCT_LIST_PRESENT_ENTITIES
    )
    assert ChatOperationalResponseProfileService.LMP_PRESENT_ENTITIES
    assert ChatOperationalResponseProfileService.SYSTEM_PRESENT_ENTITIES


def test_is_entity_routed_for_present_includes_kpi_and_sql() -> None:
    assert ChatOperationalResponseProfileService.is_entity_routed_for_present(
        "financial_rol"
    )
    assert ChatOperationalResponseProfileService.is_entity_routed_for_present("sql_result")
    assert ChatOperationalResponseProfileService.is_entity_routed_for_present(
        "product_billing"
    )


def test_enrich_humanized_does_not_append_meta_fields_glossary() -> None:
    enriched = ChatOperationalResponseProfileService.enrich_humanized(
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
    assert enriched.get("linhas_detalhe") in (None, [])


def test_resolve_entity_and_product_operational_path() -> None:
    entity = ChatOperationalResponseProfileService.resolve_entity(
        path="/products/90269001/stock",
    )

    assert entity == "product_stock"
    assert ChatOperationalResponseProfileService.is_product_operational_path(
        "/products/90269001/stock"
    )
    assert (
        ChatOperationalResponseProfileService.operational_empty_route_key(entity)
        == "stock"
    )
    assert ChatOperationalResponseProfileService.matches_entity(
        entity,
        "product_stock",
    )


def test_entity_path_hint_for_product_analyser() -> None:
    hint = ChatOperationalResponseProfileService.entity_path_hint("product_analyser")

    assert hint == "/products/0/analyser"
    assert ChatOperationalResponseProfileService.presentation_path(
        path="",
        entity="product_analyser",
    ) == "/products/0/analyser"


def test_present_product_analyser_entity_first_without_http_path() -> None:
    from tests.fixtures.api_delpi_responses_loader import with_api_delpi_meta
    from tests.unit.application.use_cases.test_execute_external_action_analyser_presentation import (
        _raw_analyser_api_payload,
    )

    presenter = ExternalActionResultPresenter()
    envelope = with_api_delpi_meta(
        _raw_analyser_api_payload(),
        {
            "entity": "product_analyser",
            "shape": "composite_analysis",
            "operationId": "get_product_analyser",
        },
    )

    result = presenter.present(envelope, path="")

    assert result.get("titulo")
    assert isinstance(result.get("linhas"), list)


def test_entity_or_path_matches_and_no_chart_route() -> None:
    assert ChatOperationalResponseProfileService.entity_or_path_matches(
        "product_analyser",
        "/any/path",
        "product_analyser",
        path_fragments=("/analyser",),
    )
    assert ChatOperationalResponseProfileService.entity_or_path_matches(
        None,
        "/products/1/analyser",
        "product_analyser",
        path_fragments=("/analyser",),
    )
    assert ChatOperationalResponseProfileService.is_no_chart_route(
        "product_structure",
        "/products/1/structure",
    )
    assert not ChatOperationalResponseProfileService.is_no_chart_route(
        "supplies_cpv",
        "/supplies/cpv",
    )
