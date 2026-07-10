"""Revisão PDF × cadastro — confiança do carimbo antes de crítico."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


class ChatDrawingRevisionCrossCheckService:
    @classmethod
    def stamp_trusted(cls, pdf_extract: dict[str, Any] | None) -> bool:
        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}

        if pdf_meta.get("titleBlock"):
            return True

        vision = pdf_meta.get("documentVision")

        if isinstance(vision, dict) and vision.get("hasTitleBlock"):
            return True

        return False

    @classmethod
    def should_pending_instead_of_critical(
        cls,
        pdf_extract: dict[str, Any] | None,
    ) -> bool:
        if not cls._rule_bool("pendingWhenTitleBlockMissing", True):
            return False

        return not cls.stamp_trusted(pdf_extract)

    @classmethod
    def _rule_bool(cls, key: str, default: bool) -> bool:
        node = ChatDrawingPatternsService.validation_rule("revisionCrossCheck")

        if not isinstance(node, dict):
            return default

        value = node.get(key)

        if isinstance(value, bool):
            return value

        return default
