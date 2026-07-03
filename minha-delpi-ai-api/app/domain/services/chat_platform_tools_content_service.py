"""Loader canônico de ``platform_tools.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "platform_tools"


class ChatPlatformToolsContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    def format(cls, *path: str, default: str = "", **values: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            *path,
            default=default,
            **values,
        )

    @classmethod
    def list(cls, *path: str) -> tuple[str, ...]:
        return tuple(
            str(item)
            for item in ChatAssistantContentService.list(_BUNDLE, *path)
            if str(item).strip()
        )
