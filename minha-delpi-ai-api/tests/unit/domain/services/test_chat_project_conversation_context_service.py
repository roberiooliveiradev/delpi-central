from app.domain.services.chat_project_conversation_context_service import (
    ChatProjectConversationContextService,
)


def test_merge_memory_overlay_fills_missing_keys_only():
    snapshot = {
        "operationalFocus": {"branch": "01"},
        "behaviorInstructions": {"tone": "formal"},
    }
    overlay = {
        "operationalFocus": {"branch": "99", "productCode": "ABC"},
        "behaviorInstructions": {"answerLength": "short"},
    }

    merged = ChatProjectConversationContextService.merge_memory_overlay(snapshot, overlay)

    assert merged["operationalFocus"]["branch"] == "01"
    assert merged["operationalFocus"]["productCode"] == "ABC"
    assert merged["behaviorInstructions"]["tone"] == "formal"
    assert merged["behaviorInstructions"]["answerLength"] == "short"
    assert merged["projectMemoryApplied"] is True
