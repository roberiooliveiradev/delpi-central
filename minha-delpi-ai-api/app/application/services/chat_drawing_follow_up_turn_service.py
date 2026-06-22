"""Respostas diretas a chips de follow-up após análise de desenho — Onda 12 Fase 5."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from app.domain.services.chat_drawing_llm_presentation_service import (
    ChatDrawingLlmPresentationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)


class ChatDrawingFollowUpTurnService:
    @classmethod
    def resolve_direct_answer(
        cls,
        message: str | None,
        *,
        previous_messages: list | None,
        attachment_ids: list[str] | None = None,
    ) -> str | None:
        if not message or not str(message).strip():
            return None

        if ChatDrawingIntentService.is_drawing_analysis_request(
            message,
            attachment_ids=attachment_ids,
        ):
            return None

        if cls._wants_reanalysis(message):
            return None

        if cls._wants_bom_reextract(message):
            return None

        analysis = ChatDrawingLlmPresentationService.last_analysis_from_messages(
            previous_messages
        )

        if not analysis:
            return None

        normalized = str(message).casefold()

        if cls._wants_critical_only(normalized):
            return ChatDrawingValidationOrchestrationService.format_critical_only_markdown(
                analysis
            )

        if cls._wants_full_checklist(normalized):
            package = {"drawingAnalysis": analysis}
            return ChatDrawingValidationOrchestrationService.format_report_markdown(package)

        if cls._wants_bom_validation(normalized):
            return ChatDrawingValidationOrchestrationService.format_section_filter_markdown(
                analysis,
                section_keywords=("bom", "estrutura", "componente", "material"),
                title="Validação BOM — desenho DELPI",
            )

        if cls._wants_dimension_validation(normalized):
            return ChatDrawingValidationOrchestrationService.format_section_filter_markdown(
                analysis,
                section_keywords=("cota", "comprimento", "decape", "dimens"),
                title="Validação de cotas — desenho DELPI",
            )

        if cls._wants_report_repeat(normalized):
            package = {"drawingAnalysis": analysis}
            return ChatDrawingValidationOrchestrationService.format_report_markdown(package)

        return None

    @classmethod
    def _last_drawing_analysis(cls, previous_messages: list | None) -> dict[str, Any] | None:
        return ChatDrawingLlmPresentationService.last_analysis_from_messages(
            previous_messages
        )

    @classmethod
    def _wants_reanalysis(cls, message: str) -> bool:
        normalized = str(message).casefold()
        return bool(re.search(r"\breanalise\b|\bre-analise\b", normalized))

    @classmethod
    def _wants_bom_reextract(cls, message: str) -> bool:
        folded = cls._fold_accents(str(message).casefold())
        return bool(
            re.search(
                r"reextrair\s+(a\s+)?(tabela\s+de\s+materiais|bom)|"
                r"extrair\s+novamente\s+(a\s+)?bom|"
                r"reextraia\s+(a\s+)?(tabela\s+de\s+materiais|bom)",
                folded,
            )
        )

    @classmethod
    def _wants_critical_only(cls, normalized: str) -> bool:
        folded = cls._fold_accents(normalized)
        return bool(
            re.search(
                r"erros?\s+criticos?|so\s+criticos?|apenas\s+(os\s+)?erros?\s+criticos?",
                folded,
            )
        )

    @classmethod
    def _fold_accents(cls, text: str) -> str:
        import unicodedata

        decomposed = unicodedata.normalize("NFD", str(text))
        return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")

    @classmethod
    def _wants_full_checklist(cls, normalized: str) -> bool:
        return "checklist completo" in normalized or "checklist da análise" in normalized

    @classmethod
    def _wants_bom_validation(cls, normalized: str) -> bool:
        return "tabela de materiais" in normalized or "validar bom" in normalized or (
            "bom" in normalized and "desenho" in normalized
        )

    @classmethod
    def _wants_dimension_validation(cls, normalized: str) -> bool:
        return "cotas" in normalized or "decapes" in normalized or "decape" in normalized

    @classmethod
    def _wants_report_repeat(cls, normalized: str) -> bool:
        return bool(
            re.search(
                r"ger(e|ar)\s+(novamente\s+)?o\s+relat[oó]rio|relat[oó]rio\s+t[eé]cnico",
                normalized,
            )
        )
