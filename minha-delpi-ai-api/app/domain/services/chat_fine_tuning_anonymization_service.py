"""Anonimização de textos para datasets de fine-tuning (playbook Fase 7, §24)."""

from __future__ import annotations

import re

from app.domain.services.chat_learning_content_service import ChatLearningContentService
from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard

_REDACT = "[REDACTED]"


def _anonymization_patterns() -> tuple[re.Pattern[str], ...]:
    """Reutiliza catálogo JSON do safety guard para consistência."""
    return (
        *ChatLearningContentService.compile_pattern_list("secretPatterns"),
        *ChatLearningContentService.compile_pattern_list("piiPatterns"),
        ChatLearningContentService.compile_pattern("longDigitRun"),
    )


class ChatFineTuningAnonymizationService:
    @classmethod
    def anonymize(cls, text: str) -> str:
        content = str(text or "")

        for pattern in _anonymization_patterns():
            content = pattern.sub(_REDACT, content)

        return content.strip()

    @classmethod
    def anonymize_messages(cls, messages: list[dict]) -> list[dict]:
        result: list[dict] = []

        for item in messages or []:
            if not isinstance(item, dict):
                continue

            role = str(item.get("role") or "user").strip() or "user"
            content = cls.anonymize(str(item.get("content") or ""))

            if content:
                result.append({"role": role, "content": content})

        return result

    @classmethod
    def assess_risk(cls, text: str) -> dict:
        return ChatLearningSafetyGuard.inspect(text)
