"""Registry normalizado de capabilities do chat (E4.S1)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "capability_registry"


class ChatCapabilityRegistryService:
    BUNDLE = _BUNDLE

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits") or {}
        if not isinstance(node, dict):
            return default
        try:
            return int(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def scoring_float(cls, key: str, default: float) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, "scoring") or {}
        if not isinstance(node, dict):
            return default
        try:
            return float(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def scoring_int(cls, key: str, default: int) -> int:
        return int(cls.scoring_float(key, float(default)))

    @classmethod
    def discard_reason(cls, key: str, default: str) -> str:
        node = ChatAssistantContentService.get_node(_BUNDLE, "discardReasons") or {}
        if not isinstance(node, dict):
            return default
        return str(node.get(key, default) or default).strip() or default

    @classmethod
    def all_capabilities(cls) -> list[dict[str, Any]]:
        raw = ChatAssistantContentService.get_node(_BUNDLE, "capabilities") or []
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict) and item.get("capabilityId")]

    @classmethod
    def by_id(cls, capability_id: str) -> dict[str, Any] | None:
        token = str(capability_id or "").strip()
        for item in cls.all_capabilities():
            if str(item.get("capabilityId") or "").strip() == token:
                return item
        return None

    @classmethod
    def by_type(cls, capability_type: str) -> list[dict[str, Any]]:
        wanted = str(capability_type or "").strip().lower()
        return [
            item
            for item in cls.all_capabilities()
            if str(item.get("type") or "").strip().lower() == wanted
        ]

    @classmethod
    def count(cls) -> int:
        return len(cls.all_capabilities())
