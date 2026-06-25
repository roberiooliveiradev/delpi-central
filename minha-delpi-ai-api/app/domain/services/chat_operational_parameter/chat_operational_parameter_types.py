"""Tipos e conteúdo — parâmetros operacionais."""

from __future__ import annotations

from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@lru_cache(maxsize=1)
def _parameter_content() -> dict:
    return ChatAssistantContentService.load_bundle("operational_parameters")
