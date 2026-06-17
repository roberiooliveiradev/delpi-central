from app.domain.services.production.production_consumption_top_items_group_by_service import (
    ProductionConsumptionTopItemsGroupByService,
)


def test_group_by_registry_contains_expected_dimensions() -> None:
    allowed = ProductionConsumptionTopItemsGroupByService.allowed_keys()

    assert {"general", "branch", "product_group", "unit", "branch_summary"}.issubset(
        allowed
    )


def test_normalize_unknown_group_by_falls_back_to_general() -> None:
    assert ProductionConsumptionTopItemsGroupByService.normalize("invalid") == "general"


def test_render_select_fields_substitutes_consumption_expression() -> None:
    spec = ProductionConsumptionTopItemsGroupByService.resolve("unit")
    rendered = ProductionConsumptionTopItemsGroupByService.render_select_fields(
        spec,
        consumption_expr="SUM_TEST",
    )

    assert "SUM_TEST" in rendered
    assert "SB1.B1_UM AS unit" in rendered
