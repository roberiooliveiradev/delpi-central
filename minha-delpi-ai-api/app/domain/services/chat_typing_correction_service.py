"""Sugestões determinísticas de correção de digitação no composer (Playbook 14)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_PROTECTED_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b\d{5,}\b"), "product_code"),
    (re.compile(r"@\S+"), "mention"),
    (re.compile(r"`[^`]+`"), "backtick"),
    (
        re.compile(
            r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b[\s\S]*?(?=\n\n|\Z|;)",
            re.IGNORECASE,
        ),
        "sql",
    ),
)

_CORRIJA_PATTERN = re.compile(r"corrija\s*:", re.IGNORECASE)


class ChatTypingCorrectionService:
    """Diff token a token sobre regras do normalizador, com spans protegidos."""

    MAX_CHANGES = 3

    @classmethod
    def suggest(cls, text: str) -> dict[str, Any]:
        raw = str(text or "")

        if not raw.strip():
            return cls._empty_result(raw)

        protected = cls._collect_protected_spans(raw)
        corrija_end = cls._corrija_zone_end(raw)
        candidates: list[tuple[int, int, str, str, str]] = []

        for pattern, replacement in ChatMessageNormalizationService.iter_typo_patterns():
            for match in pattern.finditer(raw):
                start, end = match.start(), match.end()

                if corrija_end is not None and start >= corrija_end:
                    continue

                if cls._overlaps_protected(start, end, protected):
                    continue

                matched = raw[start:end]

                try:
                    expanded = match.expand(replacement)
                except re.error:
                    continue

                preserved = cls._preserve_case(matched, expanded)

                if preserved == matched:
                    continue

                candidates.append((start, end, matched, preserved, "typo_rule"))

        selected = cls._select_non_overlapping(candidates, max_count=cls.MAX_CHANGES)

        if not selected:
            return {
                "hasSuggestions": False,
                "corrected": raw,
                "original": raw,
                "changes": [],
                "protectedSpans": protected,
            }

        corrected = raw
        for start, end, _matched, preserved, _kind in sorted(
            selected,
            key=lambda item: item[0],
            reverse=True,
        ):
            corrected = corrected[:start] + preserved + corrected[end:]

        changes = [
            {
                "offset": start,
                "length": end - start,
                "replacement": preserved,
                "from": matched,
                "to": preserved,
                "kind": kind,
            }
            for start, end, matched, preserved, kind in sorted(
                selected,
                key=lambda item: item[0],
            )
        ]

        return {
            "hasSuggestions": corrected != raw,
            "corrected": corrected,
            "original": raw,
            "changes": changes,
            "protectedSpans": protected,
        }

    @staticmethod
    def _empty_result(text: str) -> dict[str, Any]:
        return {
            "hasSuggestions": False,
            "corrected": text,
            "original": text,
            "changes": [],
            "protectedSpans": [],
        }

    @classmethod
    def _collect_protected_spans(cls, text: str) -> list[dict[str, Any]]:
        spans: list[tuple[int, int, str]] = []

        for pattern, reason in _PROTECTED_PATTERNS:
            for match in pattern.finditer(text):
                spans.append((match.start(), match.end(), reason))

        if not spans:
            return []

        spans.sort(key=lambda item: (item[0], item[1]))
        merged: list[tuple[int, int, str]] = []

        for start, end, reason in spans:
            if not merged:
                merged.append((start, end, reason))
                continue

            prev_start, prev_end, prev_reason = merged[-1]

            if start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, end), prev_reason)
                continue

            merged.append((start, end, reason))

        return [
            {"start": start, "end": end, "reason": reason}
            for start, end, reason in merged
        ]

    @staticmethod
    def _corrija_zone_end(text: str) -> int | None:
        match = _CORRIJA_PATTERN.search(text)
        return match.end() if match else None

    @staticmethod
    def _overlaps_protected(start: int, end: int, protected: list[dict[str, Any]]) -> bool:
        for span in protected:
            span_start = int(span.get("start", -1))
            span_end = int(span.get("end", -1))

            if start < span_end and end > span_start:
                return True

        return False

    @staticmethod
    def _select_non_overlapping(
        candidates: list[tuple[int, int, str, str, str]],
        *,
        max_count: int,
    ) -> list[tuple[int, int, str, str, str]]:
        if not candidates:
            return []

        ordered = sorted(
            candidates,
            key=lambda item: (item[0], -(item[1] - item[0])),
        )
        selected: list[tuple[int, int, str, str, str]] = []

        for candidate in ordered:
            start, end, *_rest = candidate

            if any(start < other_end and end > other_start for other_start, other_end, *_ in selected):
                continue

            selected.append(candidate)

            if len(selected) >= max_count:
                break

        return selected

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
