"""whenNotToUse do contrato OpenAPI — extração, strip do haystack positivo e match negativo.

Fonte: campo whenNotToUse / when_not_to_use, ou cláusula «Do not use» / «Não use»
dobrada na description no import (sem coluna dedicada no catálogo persistido).

Não contém path/operationId de domínio. Quoted examples no contrato são o sinal.
"""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)

_QUOTE_RE = re.compile(
    r"«([^»]{3,})»|“([^”]{3,})”|\"([^\"]{3,})\"|'([^']{3,})'"
)
_PLACEHOLDER_RE = re.compile(r"\b(x|n|nn|code|id|sku)\b", re.IGNORECASE)
_MULTI_SPACE_RE = re.compile(r"\s+")


class OpenApiWhenNotToUseGuidanceService:
    @classmethod
    def resolve(cls, action: dict[str, Any] | None) -> str:
        if not isinstance(action, dict):
            return ""
        explicit = str(
            action.get("whenNotToUse") or action.get("when_not_to_use") or ""
        ).strip()
        if explicit:
            return explicit
        description = str(action.get("description") or "")
        return cls.extract_clause(description)

    @classmethod
    def extract_clause(cls, text: str) -> str:
        raw = str(text or "")
        if not raw.strip():
            return ""
        lowered = raw.lower()
        best_pos = -1
        for marker in cls._clause_markers():
            pos = lowered.find(marker.lower())
            if pos >= 0 and (best_pos < 0 or pos < best_pos):
                best_pos = pos
        if best_pos < 0:
            return ""
        return raw[best_pos:].strip()

    @classmethod
    def description_for_positive_match(cls, action: dict[str, Any] | None) -> str:
        if not isinstance(action, dict):
            return ""
        description = str(action.get("description") or "").strip()
        if not description:
            return ""
        clause = cls.resolve(action)
        if clause:
            stripped = cls._remove_once(description, clause)
            if stripped != description:
                return stripped.strip(" .")
        extracted = cls.extract_clause(description)
        if extracted:
            return cls._remove_once(description, extracted).strip(" .")
        return description

    @classmethod
    def quoted_negative_phrases(cls, action: dict[str, Any] | None) -> tuple[str, ...]:
        return cls._quoted_phrases(cls.resolve(action))

    @classmethod
    def quoted_positive_phrases(cls, action: dict[str, Any] | None) -> tuple[str, ...]:
        if not isinstance(action, dict):
            return ()
        when_to = str(action.get("whenToUse") or action.get("when_to_use") or "")
        positive = cls.description_for_positive_match(action)
        negative = set(cls.quoted_negative_phrases(action))
        return tuple(
            phrase
            for phrase in cls._quoted_phrases(f"{when_to} {positive}")
            if phrase not in negative
        )

    @classmethod
    def matches_message(cls, message: str, action: dict[str, Any] | None) -> bool:
        return cls._message_has_phrase(message, cls.quoted_negative_phrases(action))

    @classmethod
    def matches_positive(cls, message: str, action: dict[str, Any] | None) -> bool:
        return cls._message_has_phrase(message, cls.quoted_positive_phrases(action))

    @classmethod
    def penalty(cls, message: str, action: dict[str, Any] | None) -> float:
        if not cls.matches_message(message, action):
            return 0.0
        return OpenApiToolRoutingContentService.float_setting(
            "whenNotToUse",
            "penalty",
            default=3.0,
        )

    @classmethod
    def bonus(cls, message: str, action: dict[str, Any] | None) -> float:
        if not cls.matches_positive(message, action):
            return 0.0
        return OpenApiToolRoutingContentService.float_setting(
            "whenNotToUse",
            "positiveReward",
            default=3.0,
        )

    @classmethod
    def filter_candidates(
        cls,
        message: str,
        candidates: list[Any],
        *,
        raw_action_of,
    ) -> list[Any]:
        """Drop candidates whose quoted whenNotToUse matches; fail-soft if all match."""
        if not candidates:
            return candidates
        kept = [
            item
            for item in candidates
            if not cls.matches_message(message, raw_action_of(item))
        ]
        return kept if kept else list(candidates)

    @classmethod
    def prefer_candidates(
        cls,
        message: str,
        candidates: list[Any],
        *,
        raw_action_of,
    ) -> list[Any]:
        """Keep candidates whose quoted whenToUse matches; fail-soft if none match."""
        if not candidates:
            return candidates
        matched = [
            item
            for item in candidates
            if cls.matches_positive(message, raw_action_of(item))
        ]
        return matched if matched else list(candidates)

    @classmethod
    def _quoted_phrases(cls, text: str) -> tuple[str, ...]:
        clause = str(text or "")
        if not clause.strip():
            return ()
        min_chars = OpenApiToolRoutingContentService.int_setting(
            "whenNotToUse",
            "minQuotedPhraseChars",
            default=5,
        )
        phrases: list[str] = []
        seen: set[str] = set()
        for match in _QUOTE_RE.finditer(clause):
            raw = next((group for group in match.groups() if group), "") or ""
            needle = cls._normalize_phrase(raw)
            if len(needle) < min_chars:
                continue
            if needle in seen:
                continue
            seen.add(needle)
            phrases.append(needle)
        return tuple(phrases)

    @classmethod
    def _message_has_phrase(cls, message: str, phrases: tuple[str, ...]) -> bool:
        if not phrases:
            return False
        haystack = ChatMessageNormalizationService.normalize_for_matching(message)
        if not haystack:
            haystack = ChatMessageNormalizationService.strip_accents(message)
        if not haystack:
            return False
        return any(phrase in haystack for phrase in phrases)

    @classmethod
    def _normalize_phrase(cls, phrase: str) -> str:
        needle = ChatMessageNormalizationService.strip_accents(phrase)
        needle = _PLACEHOLDER_RE.sub(" ", needle)
        needle = _MULTI_SPACE_RE.sub(" ", needle).strip()
        return needle

    @classmethod
    def _clause_markers(cls) -> tuple[str, ...]:
        configured = OpenApiToolRoutingContentService.list_setting(
            "whenNotToUse",
            "clauseMarkers",
        )
        if configured:
            return tuple(configured)
        return ("Do not use", "Não use", "Nao use")

    @classmethod
    def _remove_once(cls, source: str, fragment: str) -> str:
        if not fragment:
            return source
        idx = source.lower().find(fragment.lower())
        if idx < 0:
            return source
        return (source[:idx] + source[idx + len(fragment) :]).strip()
