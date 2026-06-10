"""Confirmação de termos ambíguos — playbook §9, §27 (baixa confiança)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_term_extraction_service import ChatTermExtractionService
from app.domain.services.chat_vocabulary_learning_service import (
    ChatVocabularyLearningService,
)

_BUNDLE = "learning_content"
_CONFIRMATION_THRESHOLD = 0.5
_PENDING_KEY = "learningTermConfirmation"


class ChatLearningTermAmbiguityService:
    @staticmethod
    def confirmation_threshold() -> float:
        return _CONFIRMATION_THRESHOLD

    @classmethod
    def needs_confirmation(cls, confidence: float | None) -> bool:
        if confidence is None:
            return True

        return float(confidence) < cls.confirmation_threshold()

    @classmethod
    def get_pending(cls, working_memory: dict | None) -> dict | None:
        if not isinstance(working_memory, dict):
            return None

        pending = working_memory.get(_PENDING_KEY)

        if not isinstance(pending, dict):
            return None

        term = str(pending.get("term") or "").strip()

        if not term:
            return None

        return pending

    @classmethod
    def build_pending_patch(
        cls,
        *,
        term: str,
        proposed_meaning: str | None,
        confidence: float,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            _PENDING_KEY: {
                "term": str(term).strip(),
                "proposedMeaning": str(proposed_meaning or "").strip() or None,
                "confidence": float(confidence),
                "sources": list(sources or [])[:3],
            }
        }

    @classmethod
    def clear_pending_patch(cls) -> dict[str, Any]:
        return {_PENDING_KEY: None}

    @classmethod
    def format_known_definition(cls, *, term: str, meaning: str) -> str:
        template = ChatAssistantContentService.get(
            _BUNDLE,
            "termConfirmation",
            "knownDefinition",
        )
        return template.format(term=term, meaning=meaning)

    @classmethod
    def format_proposed_meaning_prompt(
        cls,
        *,
        term: str,
        meaning: str,
    ) -> str:
        template = ChatAssistantContentService.get(
            _BUNDLE,
            "termConfirmation",
            "proposedMeaning",
        )
        return template.format(term=term, meaning=meaning)

    @classmethod
    def format_unknown_term_prompt(cls, *, term: str) -> str:
        template = ChatAssistantContentService.get(
            _BUNDLE,
            "termConfirmation",
            "unknownTerm",
        )
        return template.format(term=term)

    @classmethod
    def format_confirmation_ack(cls, *, kind: str, term: str) -> str:
        key = {
            "confirmed": "confirmed",
            "corrected": "corrected",
            "rejected": "rejected",
        }.get(kind, "confirmed")

        template = ChatAssistantContentService.get(
            _BUNDLE,
            "termConfirmation",
            key,
        )
        return template.format(term=term)

    @classmethod
    def parse_confirmation_reply(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        affirmative = ChatAssistantContentService.get_node(
            _BUNDLE,
            "confirmationReplies",
            "affirmative",
        )
        negative = ChatAssistantContentService.get_node(
            _BUNDLE,
            "confirmationReplies",
            "negative",
        )

        if isinstance(affirmative, list):
            for token in affirmative:
                if normalized == str(token).strip().lower():
                    return "confirm"

        if isinstance(negative, list):
            for token in negative:
                if normalized == str(token).strip().lower():
                    return "reject"

        if normalized.startswith(("sim", "confirmo")):
            return "confirm"

        if normalized.startswith(("nao", "não")):
            return "reject"

        return None

    @classmethod
    def extract_explicit_meaning_for_term(
        cls,
        message: str,
        *,
        term: str,
    ) -> str | None:
        definition = ChatVocabularyLearningService.detect_explicit_definition(message or "")

        if definition:
            defined_term = str(definition.get("term") or "").strip()
            meaning = str(definition.get("meaning") or "").strip()

            if (
                defined_term
                and meaning
                and ChatTermExtractionService.normalize(defined_term)
                == ChatTermExtractionService.normalize(term)
            ):
                return meaning

        patterns = (
            re.compile(
                rf"^(?:{re.escape(term)})\s+(?:significa|quer dizer|e|é)\s+(?P<meaning>.+)$",
                re.IGNORECASE,
            ),
            re.compile(
                r"^(?:significa|quer dizer)\s+(?P<meaning>.+)$",
                re.IGNORECASE,
            ),
        )

        raw = (message or "").strip()

        for pattern in patterns:
            match = pattern.match(raw)

            if match:
                meaning = str(match.group("meaning") or "").strip(" .!?")

                if meaning:
                    return meaning

        return None
