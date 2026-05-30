"""Heurísticas e disponibilidade da tool interna web_search."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.config.settings import Settings


class ChatWebSearchIntentService:
    _TRIGGER_TERMS = (
        "pesquise na internet",
        "pesquisa na internet",
        "busque na internet",
        "busca na internet",
        "pesquise na web",
        "pesquisa na web",
        "busque na web",
        "busca na web",
        "pesquise online",
        "pesquisa online",
        "google",
        "duckduckgo",
        "na internet sobre",
        "web sobre",
    )

    _STRIP_PATTERNS = (
        r"^(?:por favor[, ]*)?",
        r"^(?:me )?",
        r"^(?:pode )?",
        r"^(?:voce |você )?",
        r"(?:pesquise|pesquisa|busque|busca)(?: na internet| na web| online)?(?: sobre| por)?",
        r"(?:na internet|na web|online)",
        r"(?:sobre|por)\s+",
    )

    @classmethod
    def is_feature_enabled(cls) -> bool:
        if not Settings.CHAT_WEB_SEARCH_ENABLED:
            return False

        from app.application.services.chat_intelligence_settings_service import (
            ChatIntelligenceSettingsService,
        )

        resolved = ChatIntelligenceSettingsService().resolve()
        return bool(resolved.web_search_enabled)

    @classmethod
    def matches(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        return bool(normalized) and any(term in normalized for term in cls._TRIGGER_TERMS)

    @classmethod
    def blocks_external_action_selection(cls, message: str) -> bool:
        """Busca explícita na web não dispara actions OpenAPI no mesmo turno."""
        if not cls.is_feature_enabled():
            return False

        return cls.matches(str(message or "").strip())

    @classmethod
    def resolve(cls, message: str) -> dict | None:
        if not cls.is_feature_enabled():
            return None

        raw = str(message or "").strip()

        if not raw or not cls.matches(raw):
            return None

        query = cls.extract_query(raw)

        if not query:
            return None

        return {
            "name": "web_search",
            "arguments": {"query": query},
            "reason": "A pergunta solicita informação pública na internet.",
        }

    @classmethod
    def extract_query(cls, message: str) -> str:
        query = str(message or "").strip()
        normalized = ChatMessageNormalizationService.normalize_for_matching(query) or query

        for pattern in cls._STRIP_PATTERNS:
            normalized = re.sub(pattern, " ", normalized, flags=re.IGNORECASE).strip()

        normalized = re.sub(r"\s+", " ", normalized).strip(" ?.")

        return normalized or query
