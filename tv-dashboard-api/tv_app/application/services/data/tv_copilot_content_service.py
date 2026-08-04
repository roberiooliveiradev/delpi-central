"""Conteúdo PT do copiloto TV (patches tipados)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "tv_copilot_content.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


class TvCopilotContentService:
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
    def allowed_ops(cls) -> frozenset[str]:
        raw = _load().get("allowedOps") or []
        return frozenset(str(item).strip() for item in raw if str(item).strip())
