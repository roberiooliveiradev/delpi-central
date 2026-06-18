from app.domain.features.chat_project_collaboration import (
    PROJECT_COLLABORATION_ENABLED,
    is_project_collaboration_enabled,
)
from app.domain.services.chat_project_settings_service import ChatProjectSettingsService


def test_project_collaboration_disabled_by_default():
    assert PROJECT_COLLABORATION_ENABLED is False
    assert is_project_collaboration_enabled() is False


def test_share_conversation_context_ignored_when_collaboration_disabled():
    assert ChatProjectSettingsService.share_conversation_context_enabled(
        {"shareConversationContext": True},
    ) is False

    merged = ChatProjectSettingsService.merge_metadata(
        {},
        share_conversation_context=True,
    )

    assert "shareConversationContext" not in merged
