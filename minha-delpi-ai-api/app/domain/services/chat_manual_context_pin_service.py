"""Pins manuais de contexto (filial, armazém, produto) na memória de sessão."""

from __future__ import annotations

from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntentService

_PINNABLE_KINDS = frozenset({"branch", "warehouse", "product"})

_KIND_TO_ENTITY_KEY = {
    "branch": "branch",
    "warehouse": "warehouse",
    "product": "productCode",
}

_ENTITY_KEY_TO_KIND = {value: key for key, value in _KIND_TO_ENTITY_KEY.items()}


class ChatManualContextPinService:
    @classmethod
    def is_pinnable_kind(cls, kind: str | None) -> bool:
        return str(kind or "").strip().lower() in _PINNABLE_KINDS

    @classmethod
    def entity_key_for_kind(cls, kind: str) -> str | None:
        return _KIND_TO_ENTITY_KEY.get(str(kind or "").strip().lower())

    @classmethod
    def kind_for_entity_key(cls, entity_key: str) -> str | None:
        return _ENTITY_KEY_TO_KIND.get(str(entity_key or "").strip())

    @classmethod
    def normalize_pin(cls, *, kind: str, value: str) -> tuple[str, str] | None:
        normalized_kind = str(kind or "").strip().lower()
        raw_value = str(value or "").strip()

        if not cls.is_pinnable_kind(normalized_kind) or not raw_value:
            return None

        if normalized_kind == "product":
            normalized_value = ChatProductQueryIntentService.normalize_product_code(raw_value)

            if not ChatProductQueryIntentService.is_plausible_product_code(normalized_value):
                return None

            return normalized_kind, normalized_value

        if normalized_kind in {"branch", "warehouse"}:
            token = raw_value.upper()

            if len(token) > 12:
                return None

            return normalized_kind, token

        return None

    @classmethod
    def build_chip(cls, *, kind: str, value: str) -> dict[str, str] | None:
        normalized = cls.normalize_pin(kind=kind, value=value)

        if not normalized:
            return None

        chip_kind, chip_value = normalized

        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        label = ChatUserContextItemService.neutral_entity_label(chip_kind, chip_value)

        return {
            "label": label,
            "kind": ChatUserContextItemService.chip_kind_for_display(chip_kind),
            "value": chip_value,
        }

    @classmethod
    def chips_from_overlay(cls, overlay: dict | None) -> list[dict[str, str]]:
        if not overlay:
            return []

        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        return ChatUserContextItemService.chips_from_items(
            overlay.get("userContextItems"),
        )
