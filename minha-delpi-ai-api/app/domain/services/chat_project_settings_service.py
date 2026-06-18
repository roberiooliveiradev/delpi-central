"""Configurações de projeto armazenadas em ``metadata`` (JSONB)."""

from __future__ import annotations

from typing import Any

from app.domain.features.chat_project_collaboration import is_project_collaboration_enabled

SHARE_CONVERSATION_CONTEXT_KEY = "shareConversationContext"


class ChatProjectSettingsService:
    @classmethod
    def share_conversation_context_enabled(cls, metadata: dict[str, Any] | None) -> bool:
        if not is_project_collaboration_enabled():
            return False

        if not isinstance(metadata, dict):
            return False

        return bool(metadata.get(SHARE_CONVERSATION_CONTEXT_KEY))

    @classmethod
    def merge_metadata(
        cls,
        existing: dict[str, Any] | None,
        *,
        patch: dict[str, Any] | None = None,
        share_conversation_context: bool | None = None,
    ) -> dict[str, Any]:
        merged = dict(existing or {})

        if isinstance(patch, dict):
            merged.update(patch)

        if share_conversation_context is not None:
            if is_project_collaboration_enabled():
                merged[SHARE_CONVERSATION_CONTEXT_KEY] = bool(share_conversation_context)
            else:
                merged.pop(SHARE_CONVERSATION_CONTEXT_KEY, None)

        return merged
