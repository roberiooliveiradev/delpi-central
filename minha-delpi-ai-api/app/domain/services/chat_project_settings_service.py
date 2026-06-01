"""Configurações de projeto armazenadas em ``metadata`` (JSONB)."""

from __future__ import annotations

from typing import Any

SHARE_CONVERSATION_CONTEXT_KEY = "shareConversationContext"


class ChatProjectSettingsService:
    @classmethod
    def share_conversation_context_enabled(cls, metadata: dict[str, Any] | None) -> bool:
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
            merged[SHARE_CONVERSATION_CONTEXT_KEY] = bool(share_conversation_context)

        return merged
