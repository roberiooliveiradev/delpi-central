"""Vocabulário e configuração da skill document-vision-delpi — bundle document_vision.json."""

from __future__ import annotations

import re

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "document_vision"
_COMPILED_PATTERNS: list[re.Pattern[str]] | None = None
_COMPILED_DESCRIBE_PATTERNS: list[re.Pattern[str]] | None = None


class ChatDocumentVisionContentService:
    @classmethod
    def min_message_length(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "intent",
            "minMessageLength",
            default="8",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 8

    @classmethod
    def read_content_patterns(cls) -> tuple[re.Pattern[str], ...]:
        global _COMPILED_PATTERNS

        if _COMPILED_PATTERNS is None:
            patterns = ChatAssistantContentService.list(
                _BUNDLE,
                "intent",
                "readContentPatterns",
            )
            _COMPILED_PATTERNS = [
                re.compile(str(item), re.IGNORECASE)
                for item in patterns
                if str(item).strip()
            ]

        return tuple(_COMPILED_PATTERNS)

    @classmethod
    def describe_image_patterns(cls) -> tuple[re.Pattern[str], ...]:
        global _COMPILED_DESCRIBE_PATTERNS

        if _COMPILED_DESCRIBE_PATTERNS is None:
            patterns = ChatAssistantContentService.list(
                _BUNDLE,
                "intent",
                "describeImagePatterns",
            )
            _COMPILED_DESCRIBE_PATTERNS = [
                re.compile(str(item), re.IGNORECASE)
                for item in patterns
                if str(item).strip()
            ]

        return tuple(_COMPILED_DESCRIBE_PATTERNS)

    @classmethod
    def vision_purpose(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "purposes",
            key,
            default=key,
        )

    @classmethod
    def vlm_prompt(cls, purpose: str, *, is_image: bool = False) -> str:
        normalized = str(purpose or "").strip().lower()

        if normalized == cls.vision_purpose("hybrid"):
            prompt_key = "hybrid"
        elif normalized == cls.vision_purpose("describe"):
            prompt_key = "describeImage" if is_image else "describeDocument"
        else:
            prompt_key = "ocr"

        return ChatAssistantContentService.get(
            _BUNDLE,
            "vlm",
            "prompts",
            prompt_key,
            default="",
        )

    @classmethod
    def context_label(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "context",
            key,
            default=key,
        )

    @classmethod
    def image_extensions(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(_BUNDLE, "supported", "imageExtensions")
        return tuple(str(item).strip().lower() for item in items if str(item).strip())

    @classmethod
    def document_mime_prefixes(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _BUNDLE,
            "supported",
            "documentMimePrefixes",
        )
        return tuple(str(item).strip().lower() for item in items if str(item).strip())

    @classmethod
    def activation_mode(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "activation",
            "modes",
            key,
            default=key,
        )

    @classmethod
    def activation_reason(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "activation",
            "reasons",
            key,
            default=key,
        )
