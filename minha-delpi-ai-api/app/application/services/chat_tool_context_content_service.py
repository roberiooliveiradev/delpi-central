"""Textos do pipeline de tool context — bundle tool_context.json."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatToolContextContentService:
    _BUNDLE = "tool_context"

    @classmethod
    def get(cls, *path: str) -> str:
        return ChatAssistantContentService.get(cls._BUNDLE, *path)

    @classmethod
    def format(cls, *path: str, **values: str) -> str:
        return ChatAssistantContentService.format(cls._BUNDLE, *path, **values)
