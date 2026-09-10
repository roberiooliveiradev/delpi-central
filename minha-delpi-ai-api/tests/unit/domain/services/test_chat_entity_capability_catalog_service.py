from app.domain.services.chat_entity_capability_catalog_service import (
    ChatEntityCapabilityCatalogService,
)


def test_limits_are_positive():
    assert ChatEntityCapabilityCatalogService.max_extra_routes_per_turn() > 0
    assert ChatEntityCapabilityCatalogService.max_fan_out_keys() > 0


def test_enrich_goals_for_structure():
    goals = ChatEntityCapabilityCatalogService.enrich_goals_for_artifact(
        "product_structure",
        "structure",
        product_code="90260149",
    )
    labels = {goal.scope_label for goal in goals}
    assert "stock" in labels
    assert "profile" in labels


def test_enrich_artifact_group_unknown_defaults():
    assert (
        ChatEntityCapabilityCatalogService.enrich_artifact_group(
            "acme_unknown",
            "weird",
        )
        == "default"
    )
