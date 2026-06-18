from app.domain.services.chat_project_settings_service import ChatProjectSettingsService


def test_share_flag_defaults_false():
    assert ChatProjectSettingsService.share_conversation_context_enabled(None) is False
    assert ChatProjectSettingsService.share_conversation_context_enabled({}) is False


def test_merge_metadata_ignores_share_flag_when_collaboration_disabled():
    merged = ChatProjectSettingsService.merge_metadata(
        {"other": True},
        share_conversation_context=True,
    )

    assert "shareConversationContext" not in merged
    assert merged["other"] is True
