from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "seller_portfolio_messages.json"
)


@lru_cache(maxsize=1)
def load_seller_portfolio_messages() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("seller_portfolio_messages.json deve ser um objeto.")
    return payload


class SellerPortfolioMessagesContentService:
    """Loader canônico de textos PT-BR de carteiras (erros / bulk / realtime)."""

    @classmethod
    def clear_cache(cls) -> None:
        load_seller_portfolio_messages.cache_clear()

    @classmethod
    def bundle(cls) -> dict[str, Any]:
        return load_seller_portfolio_messages()

    @classmethod
    def error(cls, key: str, **values: str) -> str:
        errors = cls.bundle().get("errors") or {}
        template = str(errors.get(key) or key)
        if not values:
            return template
        try:
            return template.format(**values)
        except Exception:
            return template

    @classmethod
    def _realtime_section(cls) -> dict[str, Any]:
        section = cls.bundle().get("realtime") or {}
        return section if isinstance(section, dict) else {}

    @classmethod
    def realtime_title(cls, action: str) -> str:
        titles = cls._realtime_section().get("titles") or {}
        fallback = (cls._realtime_section().get("fallback") or {}).get("title") or "Carteira atualizada"
        return str(titles.get(action) or fallback)

    @classmethod
    def realtime_message_template(cls, action: str) -> str:
        messages = cls._realtime_section().get("messages") or {}
        fallback = (
            (cls._realtime_section().get("fallback") or {}).get("message")
            or "{actor} alterou a carteira «{display_name}»."
        )
        return str(messages.get(action) or fallback)

    @classmethod
    def realtime_tone(cls, action: str) -> str:
        tones = cls._realtime_section().get("tones") or {}
        fallback = (cls._realtime_section().get("fallback") or {}).get("tone") or "info"
        return str(tones.get(action) or fallback)
