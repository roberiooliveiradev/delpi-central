from app.application.services.chat_help_adoption_service import ChatHelpAdoptionService
from app.application.services.chat_help_self_help_telemetry_service import (
    ChatHelpSelfHelpTelemetryService,
)


def test_attach_help_self_help_metadata_for_capability_inquiry():
    metadata: dict = {}

    ChatHelpSelfHelpTelemetryService.attach_to_assistant_metadata(
        metadata,
        message="como consulto estoque?",
        workspace_context={"agent": None, "agentId": None},
        had_direct_answer=True,
    )

    block = metadata.get("helpSelfHelp")

    assert block
    assert block.get("topic") in {"stock_lookup", "capability_inquiry", "estoque"}
    assert block.get("resolved") is True
    assert block.get("source") == "capabilities"


def test_attach_help_self_help_metadata_for_good_question():
    metadata: dict = {}

    ChatHelpSelfHelpTelemetryService.attach_to_assistant_metadata(
        metadata,
        message="como faço uma boa pergunta?",
        workspace_context={"agent": None},
        had_direct_answer=True,
    )

    block = metadata.get("helpSelfHelp")

    assert block
    assert block.get("topic") == "goodQuestion"
    assert block.get("source") == "identity"


def test_attach_skips_without_direct_answer():
    metadata: dict = {}

    ChatHelpSelfHelpTelemetryService.attach_to_assistant_metadata(
        metadata,
        message="o que você pode fazer?",
        had_direct_answer=False,
    )

    assert "helpSelfHelp" not in metadata


def test_adoption_self_help_events():
    for event in (
        "self_help_feedback",
        "self_help_suggestion_clicked",
        "self_help_requested",
    ):
        result = ChatHelpAdoptionService.record(
            user_id="user-1",
            event=event,
            metadata={"topic": "canvas"},
        )

        assert result["ok"] is True
        assert result["event"] == event
