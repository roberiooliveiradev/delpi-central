"""Loader canônico do bundle ``prior_turn_facts`` (E2.S3)."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "prior_turn_facts"


class ChatPriorTurnFactsContentService:
    BUNDLE = _BUNDLE

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits")

        if not isinstance(node, dict):
            return default

        try:
            return int(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def heading(cls, key: str) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "headings", key, default="") or ""
        ).strip()

    @classmethod
    def line(cls, key: str, **values) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "lines",
            key,
            default="",
            **values,
        ).strip()

    @classmethod
    def focus_labels(cls) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(_BUNDLE, "focusLabels")

    @classmethod
    def truncation_suffix(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "truncationSuffix", default="…")
            or "…"
        )
