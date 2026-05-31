from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_help_follow_up_service import ChatHelpFollowUpService


def test_help_follow_up_for_canvas_question():
    suggestions = ChatHelpFollowUpService.build(message="como uso a lousa?")

    assert len(suggestions) >= 2
    labels = {item["label"] for item in suggestions}
    assert "Abrir lousa" in labels or "Colocar na lousa" in labels


def test_attach_help_metadata_on_capability_inquiry():
    metadata: dict = {}

    ChatHelpFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="como faço para gerar gráfico?",
    )

    assert "helpFollowUpSuggestions" in metadata
    assert len(metadata["helpFollowUpSuggestions"]) >= 2


def test_chart_help_feature_answer():
    answer = ChatCapabilitiesService.build_feature_answer(
        message="como faço para gerar gráfico?",
        workspace_context={"agent": {"name": "Test"}},
        allowed_action_ids=[],
        action_catalog=[],
    )

    assert answer is not None
    assert "gráfico" in answer.lower() or "grafico" in answer.lower()
