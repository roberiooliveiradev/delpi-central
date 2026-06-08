"""Textos da preparação de turno — bundle turn_preparation.json."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatTurnPreparationContentService:
    _BUNDLE = "turn_preparation"
    _STREAM_BUNDLE = "stream"

    @classmethod
    def get(cls, *path: str) -> str:
        return ChatAssistantContentService.get(cls._BUNDLE, *path)

    @classmethod
    def format(cls, *path: str, **values: str) -> str:
        return ChatAssistantContentService.format(cls._BUNDLE, *path, **values)

    @classmethod
    def stream_think(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            cls._STREAM_BUNDLE,
            "turnPreparation",
            "think",
            key,
        )
