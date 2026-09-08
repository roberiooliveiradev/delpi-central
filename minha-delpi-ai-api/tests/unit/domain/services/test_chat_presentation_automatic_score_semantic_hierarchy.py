from app.domain.services.chat_presentation_automatic_score_service import (
    ChatPresentationAutomaticScoreService,
)


def test_external_hierarchy_shape_boosts_tree_without_known_entity() -> None:
    scores = ChatPresentationAutomaticScoreService.compute_scores(
        data_shape={"rows": 4, "hasCategory": True, "hasNumeric": True},
        available_views=["text", "table", "tree", "chart"],
        entity="third_party_dependency_graph",
        openapi_shape="hierarchy",
    )

    assert scores["tree"] > scores["table"]
    assert scores["tree"] >= 80


def test_legacy_hierarchy_entity_remains_a_fallback_when_shape_is_missing() -> None:
    scores = ChatPresentationAutomaticScoreService.compute_scores(
        data_shape={"rows": 4, "hasCategory": True, "hasNumeric": True},
        available_views=["text", "table", "tree", "chart"],
        entity="product_structure",
        openapi_shape=None,
    )

    assert scores["tree"] > scores["table"]
    assert scores["tree"] >= 50


def test_non_hierarchy_contract_does_not_receive_semantic_tree_boost() -> None:
    scores = ChatPresentationAutomaticScoreService.compute_scores(
        data_shape={"rows": 4, "hasCategory": True, "hasNumeric": True},
        available_views=["text", "table", "tree", "chart"],
        entity="third_party_orders",
        openapi_shape="paged_list",
    )

    assert scores["tree"] < scores["table"]
    assert scores["tree"] < scores["chart"]
