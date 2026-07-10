"""Enriquecimento tardio do turno de desenho — relatório DELPI no tool_context."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingTurnEnrichmentService:
    @classmethod
    def should_enrich(
        cls,
        tool_context: dict | None,
        *,
        message: str | None,
        attachment_ids: list[str] | None = None,
    ) -> bool:
        if not isinstance(tool_context, dict):
            return False

        if tool_context.get("drawingAnalysisExport", {}).get("markdown"):
            return False

        if not ChatDrawingIntentService.is_drawing_analysis_request(
            message,
            attachment_ids=attachment_ids,
        ):
            return False

        tool_calls = tool_context.get("toolCalls") or []

        if not isinstance(tool_calls, list):
            return False

        from app.domain.services.chat_tool_context_presentation_service import (
            ChatToolContextPresentationService,
        )

        for tool_call in ChatToolContextPresentationService._successful_external_action_tool_calls(
            tool_calls
        ):
            path = str((tool_call.get("metadata") or {}).get("path") or "").lower()

            if "/analyser" in path:
                return True

        return False

    @classmethod
    def enrich_tool_context(
        cls,
        tool_context: dict | None,
        *,
        message: str | None,
        attachment_ids: list[str] | None = None,
    ) -> dict:
        if not isinstance(tool_context, dict):
            return tool_context or {}

        if not cls.should_enrich(
            tool_context,
            message=message,
            attachment_ids=attachment_ids,
        ):
            return cls._suppress_analyser_presentations(tool_context)

        product_code = (
            tool_context.get("drawingPdfExtractSummary", {}).get("productCode")
            if isinstance(tool_context.get("drawingPdfExtractSummary"), dict)
            else None
        )

        if not product_code:
            product_code = ChatProductQueryIntentService.resolve_product_code(message or "")

        if not product_code:
            for tool_call in tool_context.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                arguments = tool_call.get("arguments") or {}

                if isinstance(arguments, dict):
                    product_code = arguments.get("code") or arguments.get("productCode")

                if product_code:
                    break

        pdf_extract = None
        summary = tool_context.get("drawingPdfExtractSummary")

        if isinstance(summary, dict):
            pdf_extract = {
                key: summary.get(key)
                for key in ("productCode", "revision", "legible", "documentVision")
                if key in summary
            }

        from app.application.services.chat_tool_context_auxiliary_service import (
            ChatToolContextAuxiliaryService,
        )
        from app.application.services.chat_tool_context_external_action_formatter import (
            ChatToolContextExternalActionFormatter,
        )
        from app.domain.services.external_actions.external_action_result_presenter import (
            ExternalActionResultPresenter,
        )

        presenter = ExternalActionResultPresenter()
        auxiliary = ChatToolContextAuxiliaryService(
            presenter=presenter,
            formatter=ChatToolContextExternalActionFormatter(presenter),
        )

        payload = auxiliary._build_drawing_analysis_enrichment(
            safe_tool_calls=list(tool_context.get("toolCalls") or []),
            product_code=str(product_code or "").strip() or None,
            has_pdf_attachment=bool(attachment_ids),
            direct_answer=str(tool_context.get("directAnswer") or "").strip() or None,
            pdf_extract=pdf_extract,
        )

        if not payload:
            return cls._suppress_analyser_presentations(tool_context)

        merged = dict(tool_context)
        merged["drawingAnalysisMode"] = True

        for key in ("directAnswer", "drawingAnalysis", "drawingAnalysisExport"):
            value = payload.get(key)

            if value is not None:
                merged[key] = value

        return cls._suppress_analyser_presentations(merged)

    @classmethod
    def _suppress_analyser_presentations(cls, tool_context: dict) -> dict:
        from app.domain.services.chat_drawing_analyser_presentation_suppression_service import (
            ChatDrawingAnalyserPresentationSuppressionService,
        )

        return ChatDrawingAnalyserPresentationSuppressionService.apply(tool_context)

    @classmethod
    def resolve_report_direct_answer(cls, tool_context: dict | None) -> str | None:
        if not isinstance(tool_context, dict):
            return None

        export = tool_context.get("drawingAnalysisExport")

        if isinstance(export, dict):
            markdown = str(export.get("markdown") or "").strip()

            if markdown:
                return markdown

        direct = str(tool_context.get("directAnswer") or "").strip()

        if direct and "Relatório de Análise" in direct:
            return direct

        return None

    @classmethod
    def build_client_metadata_slice(cls, tool_context: dict | None) -> dict[str, Any]:
        if not isinstance(tool_context, dict):
            return {}

        slice_payload: dict[str, Any] = {}

        if tool_context.get("drawingAnalysisMode"):
            slice_payload["drawingAnalysisMode"] = True

        drawing = tool_context.get("drawingAnalysis")

        if isinstance(drawing, dict):
            slice_payload["drawingAnalysis"] = drawing

        export = tool_context.get("drawingAnalysisExport")

        if isinstance(export, dict) and export.get("markdown"):
            slice_payload["drawingAnalysisExport"] = export

        return slice_payload
