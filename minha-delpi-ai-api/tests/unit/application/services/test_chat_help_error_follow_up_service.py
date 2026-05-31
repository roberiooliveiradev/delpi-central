from app.application.services.chat_help_error_follow_up_service import (
    ChatHelpErrorFollowUpService,
)


def test_attach_when_issues_present():
    metadata: dict = {}

    ChatHelpErrorFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="qual o estoque do produto 999?",
        answer="Não foi possível consultar.",
        tool_calls=[],
        issues=["action_failed"],
        workspace_context={"agent": {"name": "Agente ERP"}},
    )

    suggestions = metadata.get("helpErrorFollowUpSuggestions") or []

    assert len(suggestions) >= 3
    assert metadata.get("helpContext") == "error"
    assert any("erro" in item["label"].lower() for item in suggestions)


def test_skips_on_successful_answer():
    metadata: dict = {}

    ChatHelpErrorFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="oi",
        answer="Olá! Como posso ajudar?",
        tool_calls=[],
        issues=None,
        workspace_context={},
    )

    assert "helpErrorFollowUpSuggestions" not in metadata
