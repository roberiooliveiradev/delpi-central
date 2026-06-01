from app.domain.services.chat_project_settings_service import ChatProjectSettingsService


def test_share_flag_defaults_false():
    assert ChatProjectSettingsService.share_conversation_context_enabled(None) is False
    assert ChatProjectSettingsService.share_conversation_context_enabled({}) is False


def test_merge_metadata_sets_share_flag():
    merged = ChatProjectSettingsService.merge_metadata(
        {"other": True},
        share_conversation_context=True,
    )

    assert merged["shareConversationContext"] is True
    assert merged["other"] is True
