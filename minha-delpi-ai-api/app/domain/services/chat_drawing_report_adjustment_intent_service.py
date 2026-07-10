"""Detecção de intenção de ajuste manual do relatório de desenho — Onda 16.1."""

from __future__ import annotations

from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from app.domain.services.chat_drawing_query_intent_content_service import (
    ChatDrawingQueryIntentContentService,
)


class ChatDrawingReportAdjustmentIntentService:
    @classmethod
    def matches(
        cls,
        message: str | None,
        *,
        attachment_ids: list[str] | None = None,
    ) -> bool:
        if not message or not str(message).strip():
            return False

        if ChatDrawingIntentService.is_drawing_analysis_request(
            message,
            attachment_ids=attachment_ids,
        ):
            return False

        normalized = ChatDrawingQueryIntentContentService.normalize_message(message)

        if cls._is_reanalysis(normalized):
            return False

        if cls._is_bom_reextract(normalized):
            return False

        confirm = ChatDrawingQueryIntentContentService.matches_trigger_category(
            normalized,
            "confirmManual",
        )
        dispute = ChatDrawingQueryIntentContentService.matches_trigger_category(
            normalized,
            "disputeFinding",
        )
        regenerate = ChatDrawingQueryIntentContentService.matches_trigger_category(
            normalized,
            "regenerateReport",
        )
        chip = ChatDrawingQueryIntentContentService.matches_trigger_category(
            normalized,
            "chipTriggers",
        )

        if chip:
            return True

        if confirm and dispute:
            return True

        if dispute and regenerate:
            return True

        if confirm and regenerate:
            return True

        if confirm:
            return True

        if dispute:
            return True

        return confirm and cls._mentions_adjustable_section(normalized)

    @classmethod
    def _is_reanalysis(cls, normalized: str) -> bool:
        return "reanalise" in normalized or "re-analise" in normalized

    @classmethod
    def _is_bom_reextract(cls, normalized: str) -> bool:
        import re

        return bool(
            re.search(
                r"reextrair\s+(a\s+)?(tabela\s+de\s+materiais|bom)|"
                r"extrair\s+novamente\s+(a\s+)?bom|"
                r"reextraia\s+(a\s+)?(tabela\s+de\s+materiais|bom)",
                normalized,
            )
        )

    @classmethod
    def _mentions_adjustable_section(cls, normalized: str) -> bool:
        hints = ChatDrawingQueryIntentContentService.get_node(
            "reportAdjustmentSectionHints",
        )

        if not isinstance(hints, dict):
            return False

        for phrases in hints.values():
            if not isinstance(phrases, list):
                continue

            for phrase in phrases:
                token = ChatDrawingQueryIntentContentService.normalize_message(
                    str(phrase)
                )

                if token and token in normalized:
                    return True

        return False
