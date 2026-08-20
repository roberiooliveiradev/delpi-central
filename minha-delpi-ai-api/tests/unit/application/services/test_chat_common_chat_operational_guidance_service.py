from app.application.services.chat_common_chat_operational_guidance_service import (
    ChatCommonChatOperationalGuidanceService,
)


def test_build_follow_up_suggestions_keeps_pending_query():
    items = ChatCommonChatOperationalGuidanceService.build_follow_up_suggestions(
        "qual o estoque 10080047"
    )
    assert len(items) == 1
    assert items[0]["query"] == "qual o estoque 10080047"
    assert items[0]["action"] == "activate_agent_and_resend"
    assert "agente" in items[0]["label"].lower() or "Agente" in items[0]["label"]


def test_attach_pending_only_for_guidance_stage():
    metadata: dict = {}
    ChatCommonChatOperationalGuidanceService.attach_pending_to_metadata(
        metadata,
        message="qual o estoque 10080047",
        pipeline_stages=["common_chat_operational_guidance", "direct_answer"],
    )
    assert metadata["pendingOperationalQuery"] == "qual o estoque 10080047"
    assert metadata["followUpSuggestions"]

    empty: dict = {}
    ChatCommonChatOperationalGuidanceService.attach_pending_to_metadata(
        empty,
        message="qual o estoque 10080047",
        pipeline_stages=["tools"],
    )
    assert "pendingOperationalQuery" not in empty
