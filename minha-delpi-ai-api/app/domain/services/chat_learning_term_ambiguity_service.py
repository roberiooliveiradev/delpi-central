"""Confirmação de termos ambíguos — playbook §9, §27 (baixa confiança)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_learning_content_service import ChatLearningContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_term_extraction_service import ChatTermExtractionService
from app.domain.services.chat_vocabulary_learning_service import (
    ChatVocabularyLearningService,
)


class ChatLearningTermAmbiguityService:
    @staticmethod
    def confirmation_threshold() -> float:
        return ChatLearningContentService.setting_float("confirmationThreshold", 0.5)

    @classmethod
    def pending_memory_key(cls) -> str:
        return ChatLearningContentService.setting_str(
            "pendingMemoryKey",
            "learningTermConfirmation",
        )

    @classmethod
    def needs_confirmation(cls, confidence: float | None) -> bool:
        if confidence is None:
            return True

        return float(confidence) < cls.confirmation_threshold()

    @classmethod
    def get_pending(cls, working_memory: dict | None) -> dict | None:
        if not isinstance(working_memory, dict):
            return None

        pending = working_memory.get(cls.pending_memory_key())

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
        max_sources = ChatLearningContentService.limit_int("maxPendingSources", 3)

        return {
            cls.pending_memory_key(): {
                "term": str(term).strip(),
                "proposedMeaning": str(proposed_meaning or "").strip() or None,
                "confidence": float(confidence),
                "sources": list(sources or [])[:max_sources],
            }
        }

    @classmethod
    def clear_pending_patch(cls) -> dict[str, Any]:
        return {cls.pending_memory_key(): None}

    @classmethod
    def format_known_definition(cls, *, term: str, meaning: str) -> str:
        return ChatLearningContentService.format(
            "termConfirmation",
            "knownDefinition",
            term=term,
            meaning=meaning,
        )

    @classmethod
    def format_proposed_meaning_prompt(
        cls,
        *,
        term: str,
        meaning: str,
    ) -> str:
        return ChatLearningContentService.format(
            "termConfirmation",
            "proposedMeaning",
            term=term,
            meaning=meaning,
        )

    @classmethod
    def format_unknown_term_prompt(cls, *, term: str) -> str:
        return ChatLearningContentService.format(
            "termConfirmation",
            "unknownTerm",
            term=term,
        )

    @classmethod
    def format_confirmation_ack(cls, *, kind: str, term: str) -> str:
        key = ChatLearningContentService.ack_kind_key(kind)

        return ChatLearningContentService.format(
            "termConfirmation",
            key,
            term=term,
        )

    @classmethod
    def parse_confirmation_reply(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        affirmative = ChatLearningContentService.get_node(
            "confirmationReplies",
            "affirmative",
        )
        negative = ChatLearningContentService.get_node(
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

        for prefix in ChatLearningContentService.list(
            "confirmationReplyPrefixes",
            "affirmative",
        ):
            if normalized.startswith(str(prefix).strip().lower()):
                return "confirm"

        for prefix in ChatLearningContentService.list(
            "confirmationReplyPrefixes",
            "negative",
        ):
            if normalized.startswith(str(prefix).strip().lower()):
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
            meaning = str(definition.get("meaning") or definition.get("proposedMeaning") or "").strip()

            if (
                defined_term
                and meaning
                and ChatTermExtractionService.normalize(defined_term)
                == ChatTermExtractionService.normalize(term)
            ):
                return meaning

        patterns = (
            ChatLearningContentService.compile_term_meaning_pattern(term),
            ChatLearningContentService.compile_pattern("explicitMeaningBare"),
        )
        raw = (message or "").strip()

        for pattern in patterns:
            match = pattern.match(raw)

            if match:
                meaning = str(match.group("meaning") or "").strip(" .!?")

                if meaning:
                    return meaning

        return None
