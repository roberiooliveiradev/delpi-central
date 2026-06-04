"""Anonimização de textos para datasets de fine-tuning (playbook Fase 7, §24)."""

from __future__ import annotations

import re

from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard

_REDACT = "[REDACTED]"

# Reutiliza padrões do safety guard para consistência.
from app.domain.services import chat_learning_safety_guard as _guard

_PATTERNS: tuple[re.Pattern, ...] = (
    *_guard._SECRET_PATTERNS,
    *_guard._PII_PATTERNS,
    _guard._LONG_DIGIT_RUN,
)


class ChatFineTuningAnonymizationService:
    @classmethod
    def anonymize(cls, text: str) -> str:
        content = str(text or "")

        for pattern in _PATTERNS:
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
