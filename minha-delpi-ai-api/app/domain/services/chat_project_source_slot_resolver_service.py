"""Resolve referências anafóricas a fontes do projeto (ordinal, nome parcial)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatProjectSourceSlotResolverService:
    _BUNDLE = "turn_preparation"
    _CONTENT_PREFIX = ("directAnswers", "projectSources")

    _ORDINAL_RULES: tuple[tuple[int, tuple[str, ...]], ...] = (
        (1, (r"\bprimeir[oa]\b", r"\b1º\b", r"\b1o\b")),
        (2, (r"\bsegund[oa]\b", r"\b2º\b", r"\b2o\b")),
        (3, (r"\bterceir[oa]\b", r"\b3º\b", r"\b3o\b")),
        (4, (r"\bquart[oa]\b", r"\b4º\b", r"\b4o\b")),
        (5, (r"\bquint[oa]\b", r"\b5º\b", r"\b5o\b")),
    )

    @classmethod
    def _normalized(cls, message: str | None) -> str:
        text = unicodedata.normalize("NFKD", str(message or "").casefold())
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"\s+", " ", text)
        text = text.replace("1o ", "1º ").replace("1o.", "1º.")

        return text.strip()

    @classmethod
    def _slot_phrases(cls) -> tuple[str, ...]:
        phrases = ChatAssistantContentService.list(
            cls._BUNDLE,
            *cls._CONTENT_PREFIX,
            "slotReferencePhrases",
        )

        return tuple(phrase.strip().lower() for phrase in phrases if str(phrase).strip())

    @classmethod
    def looks_like_slot_reference(cls, message: str | None) -> bool:
        normalized = cls._normalized(message)

        if not normalized:
            return False

        if any(phrase in normalized for phrase in cls._slot_phrases()):
            return True

        if re.search(r"\b(primeir|segund|terceir|quart|quint)[oa]\b", normalized):
            return True

        if re.search(r"\b[1-5](º|o)\b", normalized) and re.search(
            r"\b(arquivo|fonte|documento)\b",
            normalized,
        ):
            return True

        return False

    @classmethod
    def resolve(
        cls,
        message: str | None,
        inventory: list[dict[str, Any]] | None,
    ) -> dict[str, Any] | None:
        items = [item for item in (inventory or []) if isinstance(item, dict)]

        if not items:
            return None

        normalized = cls._normalized(message)

        if not normalized:
            return None

        for ordinal, patterns in cls._ORDINAL_RULES:
            if any(re.search(pattern, normalized) for pattern in patterns):
                if 1 <= ordinal <= len(items):
                    return dict(items[ordinal - 1])

        if re.search(r"\b(ultim[oa]|últim[oa])\b", normalized):
            return dict(items[-1])

        partial = cls._resolve_partial_title(normalized, items)

        if partial:
            return partial

        return None

    @classmethod
    def _resolve_partial_title(
        cls,
        normalized: str,
        inventory: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        candidates: list[tuple[int, dict[str, Any]]] = []

        for item in inventory:
            title_key = cls._normalized(str(item.get("title") or ""))

            if not title_key or len(title_key) < 4:
                continue

            if title_key in normalized or normalized in title_key:
                candidates.append((len(title_key), item))
                continue

            for token in re.findall(r"[a-z0-9]{4,}", title_key):
                if token in normalized:
                    candidates.append((len(token), item))
                    break

        if not candidates:
            return None

        if len({item.get("projectSourceId") for _, item in candidates}) > 1:
            best = max(candidates, key=lambda pair: pair[0])

            return dict(best[1])

        return dict(candidates[0][1])
