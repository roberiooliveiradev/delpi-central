from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)

configure_domain_infrastructure_ports()


def test_mode_catalog_has_three_modes():
    modes = ChatResponseModeContentService.mode_catalog()

    assert len(modes) == 3
    assert {item["id"] for item in modes} == {"fast", "normal", "thinker"}


def test_alias_map_resolves_rapida():
    aliases = ChatResponseModeContentService.alias_map()

    assert aliases.get("rapida") == "fast"
    assert aliases.get("pensador") == "thinker"


def test_pipeline_effect_text():
    text = ChatResponseModeContentService.pipeline_effect_text("operational_direct")

    assert "dados" in text.lower()


def test_commentary_lead_depth_by_mode():
    assert ChatResponseModeContentService.commentary_lead_depth_for_mode("fast") == "brief"
    assert ChatResponseModeContentService.commentary_lead_depth_for_mode("thinker") == "expanded"


def test_latency_target_sec_present_for_modes():
    assert ChatResponseModeContentService.latency_target_sec("fast", default=1) == 3
    assert ChatResponseModeContentService.latency_target_sec("normal", default=1) == 5
    assert ChatResponseModeContentService.latency_target_sec("thinker", default=1) == 15


def test_context_budget_node_present_for_modes():
    for mode in ("fast", "normal", "thinker"):
        node = ChatResponseModeContentService.context_budget_node(mode)
        assert isinstance(node, dict)
        assert int(node.get("historyMaxMessages") or 0) >= 1
        assert int(node.get("maxMultiActionsPerTurn") or 0) >= 1


def test_max_multi_actions_per_turn_by_mode():
    from app.domain.services.chat_response_mode_context_budget_service import (
        ChatResponseModeContextBudgetService,
    )

    assert ChatResponseModeContextBudgetService.max_multi_actions_per_turn("fast") == 1
    assert ChatResponseModeContextBudgetService.max_multi_actions_per_turn("normal") == 4
    assert ChatResponseModeContextBudgetService.max_multi_actions_per_turn("thinker") == 6
