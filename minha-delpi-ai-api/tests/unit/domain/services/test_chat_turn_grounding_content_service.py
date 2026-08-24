from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)


def test_turn_grounding_limits_positive():
    assert ChatTurnGroundingContentService.max_preview_chars() >= 100
    assert ChatTurnGroundingContentService.max_top_keys() >= 1


def test_turn_grounding_referring_to_label_with_count():
    label = ChatTurnGroundingContentService.referring_to_label(
        title="Estrutura 90260149",
        row_count=6,
    )
    assert "90260149" in label
    assert "6" in label


def test_turn_grounding_status_values():
    assert ChatTurnGroundingContentService.status_value("grounded") == "grounded"
    assert ChatTurnGroundingContentService.status_value("ungrounded") == "ungrounded"


def test_turn_grounding_trigger_lists_non_empty():
    assert ChatTurnGroundingContentService.expand_triggers()
    assert ChatTurnGroundingContentService.insight_triggers()
    assert ChatTurnGroundingContentService.fan_out_on_referent_items()


def test_turn_grounding_narrate_instruction_loaded():
    instruction = ChatTurnGroundingContentService.narrate_instruction()
    assert "português brasileiro" in instruction.lower()
    assert "inglês" in instruction.lower()
