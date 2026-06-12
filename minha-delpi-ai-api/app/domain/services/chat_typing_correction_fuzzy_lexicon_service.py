"""Correção fuzzy sobre vocabulário operacional (Playbook 14 — P14-5)."""

from __future__ import annotations

import re
import unicodedata
from typing import ClassVar

_TOKEN_PATTERN = re.compile(r"\b[^\W\d_]+\b", re.UNICODE)


class ChatTypingCorrectionFuzzyLexiconService:
    """Levenshtein conservador sobre termos do catálogo operacional."""

    MIN_TOKEN_LEN = 4
    MAX_DISTANCE_SHORT = 1
    MAX_DISTANCE_LONG = 2
    MAX_LENGTH_DELTA = 2

    _enabled: ClassVar[bool] = False
    _terms: ClassVar[tuple[str, ...]] = ()
    _ambiguous: ClassVar[frozenset[str]] = frozenset()

    @classmethod
    def configure(
        cls,
        payload: dict[str, object] | None,
        *,
        enabled: bool = False,
    ) -> None:
        terms: list[str] = []
        ambiguous: set[str] = set()

        if isinstance(payload, dict):
            raw_terms = payload.get("terms")
            raw_ambiguous = payload.get("ambiguousTokens")

            if isinstance(raw_terms, list):
                for item in raw_terms:
                    normalized = cls._normalize_token(str(item or ""))
                    if normalized:
                        terms.append(normalized)

            if isinstance(raw_ambiguous, list):
                for item in raw_ambiguous:
                    normalized = cls._normalize_token(str(item or ""))
                    if normalized:
                        ambiguous.add(normalized)

        cls._terms = tuple(dict.fromkeys(terms))
        cls._ambiguous = frozenset(ambiguous)
        cls._enabled = bool(enabled) and bool(cls._terms)

    @classmethod
    def is_enabled(cls) -> bool:
        if not cls._enabled:
            return False

        from app.domain.services.chat_domain_config_service import ChatDomainConfigService

        return ChatDomainConfigService.chat_typing_correction_fuzzy_enabled()

    @classmethod
    def term_count(cls) -> int:
        return len(cls._terms)

    @classmethod
    def collect_candidates(
        cls,
        text: str,
        *,
        protected: list[dict[str, object]],
        corrija_end: int | None,
        occupied_spans: list[tuple[int, int]],
    ) -> list[tuple[int, int, str, str, str]]:
        if not cls._enabled or not text.strip():
            return []

        candidates: list[tuple[int, int, str, str, str]] = []

        for match in _TOKEN_PATTERN.finditer(text):
            start, end = match.start(), match.end()
            token = text[start:end]

            if corrija_end is not None and start >= corrija_end:
                continue

            if cls._overlaps_span(start, end, occupied_spans):
                continue

            if cls._overlaps_protected(start, end, protected):
                continue

            replacement = cls._match_token(token)

            if replacement is None or replacement == token:
                continue

            candidates.append((start, end, token, replacement, "fuzzy_lexicon"))

        return candidates

    @classmethod
    def _match_token(cls, token: str) -> str | None:
        normalized = cls._normalize_token(token)

        if len(normalized) < cls.MIN_TOKEN_LEN:
            return None

        if normalized.isdigit():
            return None

        if normalized in cls._ambiguous:
            return None

        if normalized in cls._terms:
            return None

        max_distance = (
            cls.MAX_DISTANCE_SHORT
            if len(normalized) <= 5
            else cls.MAX_DISTANCE_LONG
        )

        best_term: str | None = None
        best_distance = max_distance + 1

        for term in cls._terms:
            if term in cls._ambiguous:
                continue

            if normalized[0] != term[0]:
                continue

            if abs(len(normalized) - len(term)) > cls.MAX_LENGTH_DELTA:
                continue

            distance = cls._levenshtein(normalized, term)

            if distance == 0 or distance > max_distance:
                continue

            if distance < best_distance or (
                distance == best_distance
                and best_term is not None
                and len(term) < len(best_term)
            ):
                best_term = term
                best_distance = distance

        if best_term is None:
            return None

        return cls._preserve_case(token, best_term)

    @staticmethod
    def _normalize_token(value: str) -> str:
        folded = unicodedata.normalize("NFKD", str(value or ""))
        stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
        return stripped.casefold()

    @staticmethod
    def _levenshtein(left: str, right: str) -> int:
        if left == right:
            return 0

        if not left:
            return len(right)

        if not right:
            return len(left)

        previous = list(range(len(right) + 1))

        for row_index, left_char in enumerate(left, start=1):
            current = [row_index]
            for col_index, right_char in enumerate(right, start=1):
                insert_cost = current[col_index - 1] + 1
                delete_cost = previous[col_index] + 1
                replace_cost = previous[col_index - 1] + (left_char != right_char)
                current.append(min(insert_cost, delete_cost, replace_cost))
            previous = current

        return previous[-1]

    @staticmethod
    def _preserve_case(original: str, replacement: str) -> str:
        if not original or not replacement:
            return replacement

        if original.isupper():
            return replacement.upper()

        if original[0].isupper() and original[1:].islower():
            return replacement.capitalize()

        if original[0].isupper():
            return replacement[0].upper() + replacement[1:]

        return replacement

    @staticmethod
    def _overlaps_span(
        start: int,
        end: int,
        spans: list[tuple[int, int]],
    ) -> bool:
        return any(start < span_end and end > span_start for span_start, span_end in spans)

    @staticmethod
    def _overlaps_protected(
        start: int,
        end: int,
        protected: list[dict[str, object]],
    ) -> bool:
        for span in protected:
            span_start = int(span.get("start", -1))
            span_end = int(span.get("end", -1))

            if start < span_end and end > span_start:
                return True

        return False
