"""Conteúdo PT do assistente de dados (builder)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "data_builder_content.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


class TvDataBuilderContentService:
    @classmethod
    def message(cls, key: str, default: str = "", **format_kwargs: Any) -> str:
        messages = _load().get("messages") or {}
        text = str(messages.get(key) or default or key)
        if format_kwargs:
            try:
                return text.format_map(format_kwargs)
            except (KeyError, ValueError):
                return text
        return text

    @classmethod
    def setting_int(cls, key: str, default: int) -> int:
        settings = _load().get("settings") or {}
        try:
            return int(settings.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def patterns(cls, key: str) -> list[re.Pattern[str]]:
        raw = (_load().get("patterns") or {}).get(key) or []
        out: list[re.Pattern[str]] = []
        for item in raw:
            try:
                out.append(re.compile(str(item), re.IGNORECASE))
            except re.error:
                continue
        return out

    @classmethod
    def matches(cls, key: str, text: str) -> bool:
        return any(pattern.search(text or "") for pattern in cls.patterns(key))

    @classmethod
    def first_group(cls, key: str, text: str) -> str | None:
        for pattern in cls.patterns(key):
            match = pattern.search(text or "")
            if match and match.lastindex:
                return str(match.group(1)).strip()
            if match:
                return match.group(0).strip()
        return None
