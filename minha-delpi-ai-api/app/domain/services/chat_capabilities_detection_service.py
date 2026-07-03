"""Detecção declarativa de perguntas sobre capacidades do chat — bundle ``capabilities``."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@lru_cache(maxsize=1)
def _detection() -> dict[str, Any]:
    content = ChatAssistantContentService.load_bundle("capabilities")

    return content.get("detection") or {}


class ChatCapabilitiesDetectionService:
    @classmethod
    def is_capabilities_question(cls, message: str) -> bool:
        detection = _detection()
        max_length = int(detection.get("maxMessageLength") or 280)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > max_length:
            return False

        question_terms = tuple(str(item) for item in (detection.get("questionTerms") or ()))

        if ChatMessageNormalizationService.contains_any(message, question_terms):
            return True

        short_help = tuple(str(item) for item in (detection.get("shortHelp") or ()))

        if normalized in short_help:
            return True

        help_prefix_max = int(detection.get("helpPrefixMaxLength") or 80)

        if (
            normalized.startswith(("ajuda ", "help "))
            and len(normalized) < help_prefix_max
            and not cls.is_help_about_topic_inquiry(message)
        ):
            return True

        capaz_tokens = tuple(str(item) for item in (detection.get("capazTokens") or ()))

        if "capaz" in normalized and any(token in normalized for token in capaz_tokens):
            return True

        return False

    @classmethod
    def is_help_about_topic_inquiry(cls, message: str) -> bool:
        detection = _detection()
        max_length = int(detection.get("helpAboutMaxLength") or 120)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or len(normalized) > max_length:
            return False

        prefixes = tuple(str(item) for item in (detection.get("helpAboutPrefixes") or ()))

        return any(normalized.startswith(prefix) for prefix in prefixes)

    @classmethod
    def is_api_action_routes_inquiry(cls, message: str) -> bool:
        detection = _detection()
        max_length = int(detection.get("apiActionRoutesMaxLength") or 120)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or len(normalized) > max_length:
            return False

        from app.domain.services.chat_platform_tool_selection_service import (
            ChatPlatformToolSelectionService,
        )

        if ChatPlatformToolSelectionService.matches_portal_routes_inquiry(message):
            return False

        terms = tuple(str(item) for item in (detection.get("apiActionRoutesTerms") or ()))

        return ChatMessageNormalizationService.contains_any(message, terms)
