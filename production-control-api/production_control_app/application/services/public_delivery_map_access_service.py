from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "delivery_map.json"
_DEFAULT_TOKEN = "aberto"


@lru_cache(maxsize=1)
def _public_delivery_map_settings() -> dict[str, Any]:
    content = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
    settings = content.get("publicDeliveryMap")
    return settings if isinstance(settings, dict) else {}


class PublicDeliveryMapAccessService:
    """Valida o token do link público do mapa de entrega (slug configurável)."""

    def token(self) -> str:
        value = str(_public_delivery_map_settings().get("token") or "").strip()
        return value or _DEFAULT_TOKEN

    def is_valid_token(self, token: str | None) -> bool:
        return str(token or "").strip().lower() == self.token().lower()

    def message(self, key: str, default: str) -> str:
        messages = _public_delivery_map_settings().get("messages")
        if not isinstance(messages, dict):
            return default
        value = str(messages.get(key) or "").strip()
        return value or default
