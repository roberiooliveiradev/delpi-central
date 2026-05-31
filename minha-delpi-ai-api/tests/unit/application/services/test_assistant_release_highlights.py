from app.application.services.assistant_capabilities_registry import (
    AssistantCapabilitiesRegistry,
)
from app.application.services.chat_help_adoption_service import ChatHelpAdoptionService


def test_list_contextual_highlights():
    highlights = AssistantCapabilitiesRegistry.list_contextual_highlights(limit=2)

    assert highlights
    assert highlights[0].get("title")
    assert highlights[0].get("releaseVersion")


def test_help_adoption_record():
    result = ChatHelpAdoptionService.record(
        user_id="user-1",
        event="help_panel_open",
        metadata={"source": "test"},
    )

    assert result["ok"] is True
    assert result["event"] == "help_panel_open"
