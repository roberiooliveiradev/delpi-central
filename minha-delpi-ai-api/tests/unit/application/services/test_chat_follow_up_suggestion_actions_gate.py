from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)


def test_hides_operational_chips_when_actions_disabled():
    suggestions = ChatFollowUpSuggestionService.build(
        message="produto 10080001",
        answer="dados do produto",
        tool_calls=[{"metadata": {"path": "/products/10080001"}}],
        workspace_context={"actionsEnabled": False},
    )

    assert suggestions == []


def test_keeps_text_chips_without_operational_actions():
    suggestions = ChatFollowUpSuggestionService.build(
        message="deixe mais curto",
        answer="texto gerado",
        tool_calls=[],
        workspace_context={"actionsEnabled": False, "textTaskCategory": "rewrite"},
    )

    assert suggestions
