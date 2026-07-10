"""Turno de ajuste manual do relatório de desenho — Onda 16.1."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_llm_presentation_service import (
    ChatDrawingLlmPresentationService,
)
from app.domain.services.chat_drawing_query_intent_content_service import (
    ChatDrawingQueryIntentContentService,
)
from app.domain.services.chat_drawing_report_adjustment_intent_service import (
    ChatDrawingReportAdjustmentIntentService,
)
from app.domain.services.chat_drawing_report_adjustment_service import (
    ChatDrawingReportAdjustmentService,
)
from app.domain.services.chat_drawing_report_adjustment_target_service import (
    ChatDrawingReportAdjustmentTargetService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)


class ChatDrawingReportAdjustmentTurnService:
    @classmethod
    def resolve_tool_context_result(
        cls,
        message: str | None,
        *,
        previous_messages: list | None,
        attachment_ids: list[str] | None = None,
    ) -> dict[str, Any] | None:
        if not message or not str(message).strip():
            return None

        if not ChatDrawingReportAdjustmentIntentService.matches(
            message,
            attachment_ids=attachment_ids,
        ):
            return None

        analysis = ChatDrawingLlmPresentationService.last_analysis_from_messages(
            previous_messages
        )

        if not analysis:
            if ChatDrawingReportAdjustmentIntentService.has_adjustment_signal(message):
                return cls._build_missing_prior_report_result(message=message)

            return None

        existing_overrides = ChatDrawingReportAdjustmentService.load_overrides(
            previous_messages
        )
        template_key = ChatDrawingReportAdjustmentTargetService.resolve_template_key(
            message,
            analysis,
        )

        if not template_key:
            if ChatDrawingReportAdjustmentTargetService.is_ambiguous(message, analysis):
                return cls._build_direct_result(
                    message=message,
                    direct_answer=ChatDrawingQueryIntentContentService.get(
                        "directAnswers",
                        "ambiguousAdjustment",
                    ),
                    analysis=analysis,
                    overrides=existing_overrides,
                )

            if cls._has_critical_only_blockers(analysis):
                return cls._build_direct_result(
                    message=message,
                    direct_answer=ChatDrawingQueryIntentContentService.get(
                        "directAnswers",
                        "overrideRejectedCritical",
                    ),
                    analysis=analysis,
                    overrides=existing_overrides,
                )

            return None

        if ChatDrawingReportAdjustmentTargetService.is_critical_target(
            template_key,
            analysis,
        ):
            return cls._build_direct_result(
                message=message,
                direct_answer=ChatDrawingQueryIntentContentService.get(
                    "directAnswers",
                    "overrideRejectedCritical",
                ),
                analysis=analysis,
                overrides=existing_overrides,
            )

        new_override = ChatDrawingReportAdjustmentService.build_override(
            template_key=template_key,
            analysis=analysis,
        )
        overrides = ChatDrawingReportAdjustmentService.merge_override_lists(
            existing_overrides,
            new_override,
        )
        updated_analysis = ChatDrawingReportAdjustmentService.apply_overrides(
            analysis,
            overrides,
        )
        package = {"drawingAnalysis": updated_analysis}
        report_markdown = ChatDrawingValidationOrchestrationService.format_report_markdown(
            package
        )

        from app.application.services.chat_drawing_report_export_service import (
            ChatDrawingReportExportService,
        )

        export_payload = ChatDrawingReportExportService.build_export_payload(
            package=package,
            report_markdown=report_markdown,
        )

        return {
            "context": "",
            "toolCalls": [],
            "nativeToolCalling": {"used": False, "providerSupports": False},
            "directAnswer": report_markdown,
            "skipRag": True,
            "drawingAnalysisMode": True,
            "drawingAnalysis": updated_analysis,
            "drawingAnalysisExport": export_payload,
            "drawingAnalysisOverrides": overrides,
            "currentMessage": str(message).strip(),
        }

    @classmethod
    def _build_missing_prior_report_result(cls, *, message: str) -> dict[str, Any]:
        return {
            "context": "",
            "toolCalls": [],
            "nativeToolCalling": {"used": False, "providerSupports": False},
            "directAnswer": ChatDrawingQueryIntentContentService.get(
                "directAnswers",
                "missingPriorDrawingReport",
            ),
            "skipRag": True,
            "currentMessage": str(message).strip(),
        }

    @classmethod
    def _build_direct_result(
        cls,
        *,
        message: str,
        direct_answer: str,
        analysis: dict[str, Any],
        overrides: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "context": "",
            "toolCalls": [],
            "nativeToolCalling": {"used": False, "providerSupports": False},
            "directAnswer": direct_answer,
            "skipRag": True,
            "drawingAnalysisMode": True,
            "drawingAnalysis": analysis,
            "currentMessage": str(message).strip(),
        }

        if overrides:
            payload["drawingAnalysisOverrides"] = overrides

        return payload

    @classmethod
    def _has_critical_only_blockers(cls, analysis: dict[str, Any]) -> bool:
        adjustable = ChatDrawingReportAdjustmentTargetService.adjustable_items(analysis)

        if adjustable:
            return False

        items = analysis.get("items") if isinstance(analysis.get("items"), list) else []

        return any(
            isinstance(item, dict)
            and str(item.get("status") or "").strip() == "critical_error"
            for item in items
        )
