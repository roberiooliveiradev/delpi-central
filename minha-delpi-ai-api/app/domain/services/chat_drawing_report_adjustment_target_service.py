"""Resolução do item alvo para override manual do relatório de desenho."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_query_intent_content_service import (
    ChatDrawingQueryIntentContentService,
)

_STATUS_CRITICAL = "critical_error"
_ADJUSTABLE = frozenset({"pending", "error"})


class ChatDrawingReportAdjustmentTargetService:
    @classmethod
    def resolve_template_key(
        cls,
        message: str | None,
        analysis: dict[str, Any],
    ) -> str | None:
        normalized = ChatDrawingQueryIntentContentService.normalize_message(message)
        explicit = cls._resolve_explicit_template_key(normalized)

        if explicit:
            return explicit

        adjustable = cls._adjustable_items(analysis)

        if len(adjustable) == 1:
            return str(adjustable[0].get("templateKey") or "").strip() or None

        section_key = cls._resolve_section_hint(normalized)

        if section_key:
            for item in adjustable:
                section = ChatDrawingQueryIntentContentService.normalize_message(
                    str(item.get("section") or "")
                )

                if section_key in section:
                    return str(item.get("templateKey") or "").strip() or None

        if len(adjustable) > 1:
            return None

        return None

    @classmethod
    def adjustable_items(cls, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        return cls._adjustable_items(analysis)

    @classmethod
    def is_ambiguous(cls, message: str | None, analysis: dict[str, Any]) -> bool:
        return cls.resolve_template_key(message, analysis) is None and bool(
            cls._adjustable_items(analysis)
        )

    @classmethod
    def is_critical_target(cls, template_key: str, analysis: dict[str, Any]) -> bool:
        for item in analysis.get("items") or []:
            if not isinstance(item, dict):
                continue

            if str(item.get("templateKey") or "").strip() != template_key:
                continue

            return str(item.get("status") or "").strip() == _STATUS_CRITICAL

        return False

    @classmethod
    def item_for_template_key(
        cls,
        template_key: str,
        analysis: dict[str, Any],
    ) -> dict[str, Any] | None:
        for item in analysis.get("items") or []:
            if not isinstance(item, dict):
                continue

            if str(item.get("templateKey") or "").strip() == template_key:
                return item

        return None

    @classmethod
    def _adjustable_items(cls, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        items = analysis.get("items") if isinstance(analysis.get("items"), list) else []
        adjustable: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            status = str(item.get("status") or "").strip()

            if status in _ADJUSTABLE:
                adjustable.append(item)

        return adjustable

    @classmethod
    def _resolve_explicit_template_key(cls, normalized_message: str) -> str | None:
        hints = ChatDrawingQueryIntentContentService.get_node(
            "reportAdjustmentTemplateHints",
        )

        if not isinstance(hints, dict):
            return None

        for template_key, phrases in hints.items():
            if not isinstance(phrases, list):
                continue

            for phrase in phrases:
                token = ChatDrawingQueryIntentContentService.normalize_message(
                    str(phrase)
                )

                if token and token in normalized_message:
                    return str(template_key)

        return None

    @classmethod
    def _resolve_section_hint(cls, normalized_message: str) -> str | None:
        hints = ChatDrawingQueryIntentContentService.get_node(
            "reportAdjustmentSectionHints",
        )

        if not isinstance(hints, dict):
            return None

        for section_label, phrases in hints.items():
            if not isinstance(phrases, list):
                continue

            for phrase in phrases:
                token = ChatDrawingQueryIntentContentService.normalize_message(
                    str(phrase)
                )

                if token and token in normalized_message:
                    return ChatDrawingQueryIntentContentService.normalize_message(
                        str(section_label)
                    )

        return None
