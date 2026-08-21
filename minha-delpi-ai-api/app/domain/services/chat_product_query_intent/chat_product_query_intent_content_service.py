"""Delegate — intenção de consulta de produto (conteúdo)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)

_INTENT_CONTENT_BUNDLE = "product_query_intent"

_PATTERN_FLAGS = {
    "zeroRecords": re.IGNORECASE,
    "specificationToken": re.IGNORECASE,
    "dateToken": re.IGNORECASE,
    "exampleCodePrefix": re.IGNORECASE,
}


class ChatProductQueryIntentContentService:
    @classmethod
    @lru_cache(maxsize=16)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(
            _INTENT_CONTENT_BUNDLE,
            "patterns",
            key,
            default="",
        )
        if not str(source or "").strip():
            raise KeyError(f"{_INTENT_CONTENT_BUNDLE}.patterns.{key} ausente")
        return re.compile(str(source), _PATTERN_FLAGS.get(key, 0))

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()

    @classmethod
    def _terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(_INTENT_CONTENT_BUNDLE, *path)
        )

    @classmethod
    def _header(cls, key: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            _INTENT_CONTENT_BUNDLE,
            "directAnswerHeaders",
            key,
            default=default,
        )

    @classmethod
    def _matches_predicate(cls, predicate: str, normalized: str) -> bool:
        from app.domain.services.operational_route_matcher_service import (
            OperationalRouteMatcherService,
        )

        return OperationalRouteMatcherService.matches_custom_predicate(
            predicate,
            normalized,
        )

    @classmethod
    def _matches_any_predicates(cls,
        predicates: list[str] | tuple[str, ...],
        normalized: str,
    ) -> bool:
        return any(ChatProductQueryIntentContentService._matches_predicate(predicate, normalized) for predicate in predicates)

    @classmethod
    def _code_from_history_predicates(cls) -> tuple[str, ...]:
        return ChatProductQueryIntentContentService._terms("codeFromHistoryPredicates")

    @classmethod
    def _message_has_any_marker(cls, normalized: str, *path: str) -> bool:
        return any(term in normalized for term in ChatProductQueryIntentContentService._terms(*path))

