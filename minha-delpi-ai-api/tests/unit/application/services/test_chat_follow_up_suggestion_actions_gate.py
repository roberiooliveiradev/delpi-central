from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)


def test_hides_operational_chips_without_user_activated_agent():
    suggestions = ChatFollowUpSuggestionService.build(
        message="produto 10080001",
        answer="dados do produto",
        tool_calls=[{"metadata": {"path": "/products/10080001"}}],
        workspace_context={
            "actionsEnabled": True,
            "userActivatedAgent": False,
        },
    )

    assert suggestions == []


def test_shows_operational_chips_when_user_activated_agent():
    suggestions = ChatFollowUpSuggestionService.build(
        message="produto 10080001",
        answer="dados do produto",
        tool_calls=[{"metadata": {"path": "/products/10080001"}}],
        workspace_context={
            "actionsEnabled": True,
            "userActivatedAgent": True,
            "workingMemory": {"operationalFocus": {"productCode": "10080001"}},
        },
    )

    labels = [item["label"] for item in suggestions]

    assert "Ver estoque" in labels


def test_keeps_generic_chips_without_user_activated_agent():
    suggestions = ChatFollowUpSuggestionService.build(
        message="?",
        answer="não encontrei registros",
        tool_calls=[],
        workspace_context={
            "actionsEnabled": True,
            "userActivatedAgent": False,
        },
    )

    labels = [item["label"] for item in suggestions]

    assert "O que você pode fazer?" in labels


def test_keeps_text_chips_without_user_activated_agent():
    suggestions = ChatFollowUpSuggestionService.build(
        message="deixe mais curto",
        answer="texto gerado",
        tool_calls=[],
        workspace_context={
            "actionsEnabled": False,
            "userActivatedAgent": False,
            "textTaskCategory": "rewrite",
        },
    )

    assert suggestions
