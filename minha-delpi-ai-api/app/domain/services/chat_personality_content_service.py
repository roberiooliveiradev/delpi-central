"""Tom e microcopy do playbook de personalidade (conteúdo determinístico)."""

from __future__ import annotations

import zlib
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ChatAssistantContentService.load_personality_playbook()


class ChatPersonalityContentService:
    @classmethod
    def pick_phrase(
        cls,
        group: str,
        *,
        seed: str = "",
        humor_level: int | None = None,
    ) -> str:
        phrases = (_playbook().get("phrases") or {}).get(group) or []

        if not isinstance(phrases, list) or not phrases:
            return ""

        cleaned = [str(item).strip() for item in phrases if str(item).strip()]

        if not cleaned:
            return ""

        if humor_level is not None and humor_level <= 0 and group in {"success", "beforeTool"}:
            return cleaned[0]

        if len(cleaned) == 1:
            return cleaned[0]

        index = zlib.adler32(seed.encode("utf-8")) % len(cleaned)

        if humor_level is not None and humor_level <= 1 and len(cleaned) > 1:
            index = index % min(2, len(cleaned))

        return cleaned[index]

    @classmethod
    def pick_variant(
        cls,
        variants: dict[str, Any],
        *,
        scope: str,
        category: str,
        seed: str,
        fallback: str = "",
    ) -> str:
        scope_block = variants.get(scope) or {}

        if not isinstance(scope_block, dict):
            return fallback

        options = scope_block.get(category) or []

        if not isinstance(options, list) or not options:
            return fallback

        cleaned = [str(item).strip() for item in options if str(item).strip()]

        if not cleaned:
            return fallback

        if len(cleaned) == 1:
            return cleaned[0]

        index = zlib.adler32(seed.encode("utf-8")) % len(cleaned)
        return cleaned[index]
