import pytest

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_route_policy_service import (
    ChatPresentationRoutePolicyService,
)
from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


@pytest.mark.parametrize(
    ("path", "expected_key"),
    [
        ("/products/90260144/structure", "tree_hierarchy"),
        ("/products/90260144/stock", "stock"),
        ("/products/90260144/analyser", "analyser"),
        ("/products/90260144/guide", "generic"),
        ("/supplies/cpv", "generic"),
        ("/supplies/stock-value", "generic"),
        ("/production/oee/series", "generic"),
        ("/production/oee", "kpi_dashboard"),
        ("/production/otd", "kpi_dashboard"),
        ("/system/tables/search", "system"),
        ("/data/sql", "sql"),
    ],
)
def test_resolve_profile_key_by_path(path: str, expected_key: str) -> None:
    assert ChatPresentationProfileService.resolve_profile_key(path) == expected_key


def test_uses_schema_first_presentation_defaults_and_legacy() -> None:
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/commercial/proposals",
        "commercial_proposals",
    )
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/products/90260144/stock",
        "product_stock",
    )
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/commercial/closing-rate",
        "sales_conversion_rate",
    )


def test_entity_profile_precedes_path_rules() -> None:
    key = ChatPresentationProfileService.resolve_profile_key(
        "/commercial/closing-rate",
        "product_stock",
    )

    assert key == "stock"


def test_resolve_entity_from_path_json_hints_and_fallbacks() -> None:
    assert (
        ChatPresentationProfileService.resolve_entity_from_path("/supplies/cpv")
        == "supplies_cpv"
    )
    assert (
        ChatPresentationProfileService.resolve_entity_from_path(
            "/products/90269001/structure"
        )
        == "product_structure"
    )
    assert (
        ChatPresentationProfileService.resolve_entity_from_path(
            "/products/90269001/stock"
        )
        == "product_stock"
    )
    assert (
        ChatPresentationProfileService.resolve_entity_from_path(
            "/commercial/branch_rol_target_pct"
        )
        == "commercial_rol_target"
    )
    assert ChatPresentationProfileService.entity_path_hint("supplies_cpv") == "/supplies/cpv"


def test_entity_sets_loaded_from_json() -> None:
    critical = ChatPresentationProfileService.entity_set("chatCritical")
    routed = ChatPresentationProfileService.entity_routed_for_present()

    assert "product_stock" in critical
    assert "supplies_cpv" in ChatPresentationProfileService.entity_set("kpiPresent")
    assert "product_stock" in routed
    assert "commercial_proposal" in routed


def test_entity_presentation_routing_operational_empty() -> None:
    assert (
        ChatPresentationProfileService.operational_empty_route_key("product_stock")
        == "stock"
    )
    assert ChatPresentationProfileService.is_product_operational_entity("product_guide")
    assert ChatPresentationProfileService.list_route_entity("product_inspection") == "inspection"
    assert ChatPresentationProfileService.is_no_chart_entity("product_guide")
    assert not ChatPresentationProfileService.is_no_chart_entity("supplies_cpv")


def test_profile_present_dispatch_registry_has_structure_exclusivity() -> None:
    routing = ChatPresentationProfileService.entity_presentation_routing()
    dispatch = routing.get("profilePresentDispatch") or {}

    assert dispatch["structure_exclusivity"]["presenterMethod"] == (
        "present_product_structure_exclusivity"
    )


def test_production_oee_detail_entity_maps_to_dashboard() -> None:
    key = ChatPresentationProfileService.resolve_profile_key(
        "/production/oee",
        "production_oee_detail",
    )

    assert key == "kpi_dashboard"


def test_production_oee_appointment_entity_maps_to_dashboard() -> None:
    key = ChatPresentationProfileService.resolve_profile_key(
        "/production/oee/appointments/12345",
        "production_oee_appointment",
    )

    assert key == "kpi_dashboard"


def test_production_schedule_today_entity_maps_to_playbook_report() -> None:
    key = ChatPresentationProfileService.resolve_effective_profile_key(
        "/production/schedule/today",
        "production_schedule_today",
    )

    assert key == "playbook_report"


def test_production_schedule_path_without_entity_maps_to_playbook_report() -> None:
    entity = ChatPresentationProfileService.resolve_entity_from_path(
        "/production/schedule/today",
    )
    key = ChatPresentationProfileService.resolve_effective_profile_key(
        "/production/schedule/today",
        entity,
    )

    assert key == "playbook_report"


def test_production_schedule_json_profile_key_is_openapi_backed_generic() -> None:
    key = ChatPresentationProfileService.resolve_profile_key(
        "/production/schedule/today",
        "production_schedule_today",
    )

    assert key == "generic"


def test_playbook_report_profile_skips_chart_policy() -> None:
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/production/schedule/today",
        entity="production_schedule_today",
        shape="playbook_report",
    )

    assert profile.get("chartPolicy") == "skip"
    assert profile.get("defaultViewPolicy") == "table_when_available"
    assert profile.get("openapiDerived") is True


def test_production_schedule_today_is_no_chart_entity() -> None:
    assert ChatPresentationProfileService.is_no_chart_entity("production_schedule_today")


def test_humanized_narrative_mode_from_profile() -> None:
    assert (
        ChatPresentationProfileService.humanized_narrative_mode(
            "/products/90260144/stock",
            "product_stock",
        )
        == "skip"
    )
    assert (
        ChatPresentationProfileService.humanized_narrative_mode(
            "/products/90260144/pricing",
            "product_pricing",
        )
        == "skip"
    )
    assert (
        ChatPresentationProfileService.humanized_narrative_mode(
            "/products/90260144/factory-status",
            "product_factory_status",
        )
        == "enrich"
    )


def test_data_answer_lead_alignment_from_profile() -> None:
    assert (
        ChatPresentationProfileService.data_answer_lead_alignment(
            "/products/90260882/structure/exclusivity",
            "product_structure_exclusivity",
        )
        == "preserve_template"
    )
    assert (
        ChatPresentationProfileService.data_answer_lead_alignment(
            "/products/90260144/stock",
            "product_stock",
        )
        == "inject"
    )


def test_resolve_default_preferred_format_stock_table() -> None:
    preferred = ChatPresentationProfileService.resolve_default_preferred_format(
        path="/products/90260144/stock",
        has_table=True,
        has_chart=True,
        has_text=True,
    )

    assert preferred == "table"


def test_resolve_default_preferred_format_structure_tree() -> None:
    preferred = ChatPresentationProfileService.resolve_default_preferred_format(
        path="/products/90260144/structure",
        has_tree=True,
        has_table=True,
        has_text=True,
    )

    assert preferred == "tree"


def test_route_policy_delegates_to_profile_service() -> None:
    assert ChatPresentationRoutePolicyService.is_stock_route("/products/1/stock")
    assert not ChatPresentationRoutePolicyService.is_stock_route("/supplies/stock-value")
    assert ChatPresentationRoutePolicyService.is_analyser_route("/products/1/analyser")
    assert ChatPresentationRoutePolicyService.is_tree_route("/products/1/structure")

    preferred = ChatPresentationRoutePolicyService.resolve_default_preferred_format(
        path="/products/90260144/guide",
        has_table=True,
        has_text=True,
    )

    assert preferred == "table"


def test_apply_visual_order_uses_profile_priority() -> None:
    decision = {"availableViews": ["chart", "table", "text"]}

    ChatPresentationProfileService.apply_visual_order(
        decision,
        path="/products/90260144/stock",
    )

    assert decision["visualOrder"][:3] == ["text", "table", "chart"]
    assert decision["presentationProfileKey"] == "stock"


def test_apply_visual_order_keeps_single_for_as_delivered_even_with_stack_policy_always() -> None:
    decision = {
        "selected": "text",
        "layoutMode": "single",
        "availableViews": ["text", "tree", "table"],
    }

    ChatPresentationProfileService.apply_visual_order(
        decision,
        path="/products/90260609/structure/exclusivity",
    )

    assert decision["layoutMode"] == "single"
    assert decision["visualOrder"][:3] == ["text", "tree", "table"]


def test_stack_plan_reads_profile_config() -> None:
    metadata = {
        "path": "/products/90260149/analyser",
        "textPresentation": {
            "markdown": "### Título\n\n**Destaques**\n\n- Um.\n\n",
        },
        "presentationDecision": {"visualOrder": ["text", "table", "tree"]},
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["tableRoleOrder"] == ["profile", "guide", "inspection", "other"]
    assert plan["presentationProfileKey"] == "analyser"


def test_stack_plan_stock_path_uses_stock_roles() -> None:
    metadata = {
        "path": "/products/90260149/stock",
        "textPresentation": {"markdown": "**Destaques**\n\n- Saldo."},
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["tableRoleOrder"] == ["profile", "stock", "other"]
    assert plan["presentationProfileKey"] == "stock"


def test_commentary_profile_key_maps_operational_and_generic_profiles() -> None:
    assert (
        ChatPresentationProfileService.commentary_profile_key("factory_status")
        == "factory_status"
    )
    assert ChatPresentationProfileService.commentary_profile_key("stock") == "stock"
    assert (
        ChatPresentationProfileService.commentary_profile_key("table_list")
        == "generic_list"
    )
    assert (
        ChatPresentationProfileService.commentary_profile_key(
            path="/products/90260144/guide"
        )
        == "generic_list"
    )


def test_prose_delivery_mode_entity_and_profile_fallback() -> None:
    assert (
        ChatPresentationProfileService.prose_delivery_mode(
            entity="product_factory_status",
            path="/products/90269002/factory-status",
        )
        == "llm"
    )
    assert (
        ChatPresentationProfileService.prose_delivery_mode(
            entity="product_structure_exclusivity",
            path="/products/90260882/structure/exclusivity",
        )
        == "template"
    )
    assert (
        ChatPresentationProfileService.prose_delivery_mode(
            entity="production_consumption_top_items",
            path="/production/consumption/top-items",
        )
        in {"template", "llm"}
    )
    assert (
        ChatPresentationProfileService.prose_delivery_mode(
            path="/products/90260144/guide",
            entity="product_guide",
        )
        in {"template", "llm"}
    )


def test_prose_delivery_mode_entity_set_fallback(monkeypatch) -> None:
    original_node = ChatPresentationProfileService.node

    def patched_node(*keys: str):
        if keys == ("proseDeliveryByProfile",):
            return {}
        if keys == ("proseDeliveryByEntity",):
            return {}
        return original_node(*keys)

    monkeypatch.setattr(
        ChatPresentationProfileService,
        "node",
        staticmethod(patched_node),
    )

    assert (
        ChatPresentationProfileService.prose_delivery_mode(
            entity="production_consumption_top_items",
            path="/production/consumption/top-items",
        )
        == "llm"
    )


def test_prose_delivery_mode_tier_fallback(monkeypatch) -> None:
    original_node = ChatPresentationProfileService.node

    def patched_node(*keys: str):
        if keys and keys[0] in {
            "proseDeliveryByProfile",
            "proseDeliveryByEntity",
            "proseDeliveryByEntitySet",
        }:
            return {}
        return original_node(*keys)

    monkeypatch.setattr(
        ChatPresentationProfileService,
        "node",
        staticmethod(patched_node),
    )

    assert (
        ChatPresentationProfileService.prose_delivery_mode(
            entity="product_factory_status",
            path="/products/90269002/factory-status",
        )
        == "llm"
    )
    assert (
        ChatPresentationProfileService.prose_delivery_mode(
            entity="depreciation_pct",
            path="/kpi/depreciation-pct",
        )
        == "llm"
    )
