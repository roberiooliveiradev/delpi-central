"""Finalização do contexto após execução de tools — Fase 3C lote 12."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.services.chat_tool_context_execution_service import ToolExecutionState
from app.domain.services.chat_tool_context_presentation_service import (
    ChatToolContextPresentationService,
)

if TYPE_CHECKING:
    from app.application.services.chat_tool_context_service import ChatToolContextService


class ChatToolContextResultAssemblyService:
    def assemble_and_finalize(
        self,
        host: ChatToolContextService,
        *,
        message: str,
        raw_message: str,
        previous_messages: list | None,
        user_id: str,
        session_id: str | None,
        attachment_ids: list[str] | None,
        native_meta: dict,
        selected_external_action_meta: dict | None,
        execution: ToolExecutionState,
        drawing_analysis_mode: bool,
        drawing_product_code: str | None,
        drawing_product_code_source: str | None,
        drawing_has_pdf: bool,
        drawing_pdf_extract: dict | None,
        drawing_runtime_skills: dict | None,
        on_stream_activity,
    ) -> dict:
        direct_answer = execution.direct_answer
        skip_rag = execution.skip_rag
        last_external_action_data = execution.last_external_action_data
        last_web_search_data = execution.last_web_search_data
        web_sources = execution.web_sources
        web_search_payload = execution.web_search_payload
        safe_tool_calls = execution.safe_tool_calls
        pagination_continue_prompt = execution.pagination_continue_prompt
        context = execution.context

        if execution.external_action_results:
            from app.application.services.chat_composite_direct_answer_service import (
                ChatCompositeDirectAnswerService,
            )
            from app.domain.services.chat_analysis_intent_service import (
                ChatAnalysisIntentService,
            )

            if not ChatAnalysisIntentService.is_comparison_or_insight_request(raw_message):
                composite_results = [
                    item
                    for item in execution.external_action_results
                    if not (item.metadata or {}).get("sqlSchemaPrefetch")
                ]

                if composite_results:
                    direct_answer = ChatCompositeDirectAnswerService.build(
                        message,
                        composite_results,
                    )

        if isinstance(last_web_search_data, dict):
            from app.domain.services.chat_web_search_erp_cross_reference_service import (
                ChatWebSearchErpCrossReferenceService,
            )
            from app.domain.services.chat_web_search_direct_answer_service import (
                ChatWebSearchDirectAnswerService,
            )

            direct_answer, last_web_search_data = (
                ChatWebSearchErpCrossReferenceService.append_to_direct_answer(
                    direct_answer=direct_answer,
                    internal_data=last_external_action_data,
                    web_payload=last_web_search_data,
                    message=raw_message,
                )
            )
            web_search_payload = last_web_search_data

            if (
                str(last_web_search_data.get("searchStatus") or "") == "success"
                and not web_sources
            ):
                web_sources = ChatWebSearchDirectAnswerService.build_sources(
                    last_web_search_data
                )
                skip_rag = True

        if (
            not direct_answer
            and len(safe_tool_calls) == 1
            and safe_tool_calls[0].get("name") == "execute_external_action"
            and host._is_successful_external_action(safe_tool_calls[0].get("metadata") or {})
        ):
            action_metadata = safe_tool_calls[0].get("metadata") or {}
            action_arguments = safe_tool_calls[0].get("arguments") or {}
            direct_answer = host._auxiliary_service._build_direct_answer(
                host._attach_request_sql(
                    last_external_action_data,
                    action_arguments,
                    action_metadata,
                ),
                message=message,
                path=action_metadata.get("path"),
                operation_id=action_metadata.get("operationId"),
            )

        if (
            not direct_answer
            and len(safe_tool_calls) == 1
            and safe_tool_calls[0].get("name") == "web_search"
            and isinstance(last_web_search_data, dict)
        ):
            from app.domain.services.chat_web_search_direct_answer_service import (
                ChatWebSearchDirectAnswerService,
            )

            direct_answer = ChatWebSearchDirectAnswerService.format(
                last_web_search_data,
                message=raw_message,
            )

            if direct_answer:
                skip_rag = True
                web_sources = ChatWebSearchDirectAnswerService.build_sources(
                    last_web_search_data
                )
                web_search_payload = last_web_search_data

        requested_format = host._format_service.resolve_consolidation_format(
            raw_message,
            previous_messages,
            workspace_context=getattr(host, "_build_workspace_context", None),
        )
        if requested_format:
            host._format_service.apply_format_override(
                safe_tool_calls,
                requested_format,
                last_external_action_data,
            )

        if direct_answer and requested_format != "table":
            ChatToolContextPresentationService._suppress_redundant_structure_presentations(
                safe_tool_calls
            )

        if direct_answer and requested_format != "text":
            direct_answer = ChatToolContextPresentationService._compact_direct_answer_for_rich_presentation(
                direct_answer,
                safe_tool_calls,
            )

        if pagination_continue_prompt:
            direct_answer = (
                f"{direct_answer}\n\n{pagination_continue_prompt}".strip()
                if direct_answer
                else pagination_continue_prompt
            )

        from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService

        drawing_turn_active = drawing_analysis_mode or ChatDrawingIntentService.is_drawing_analysis_request(
            raw_message,
            attachment_ids=attachment_ids,
        )

        drawing_analysis_payload = None

        if drawing_turn_active:
            drawing_analysis_payload = host._auxiliary_service._build_drawing_analysis_enrichment(
                safe_tool_calls=safe_tool_calls,
                product_code=drawing_product_code,
                has_pdf_attachment=drawing_has_pdf,
                direct_answer=direct_answer,
                pdf_extract=drawing_pdf_extract,
            )

            if drawing_analysis_payload:
                direct_answer = drawing_analysis_payload.get("directAnswer") or direct_answer

            if drawing_analysis_mode and on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                ChatStreamActivityService.emit_drawing_analysis_progress(
                    on_stream_activity,
                    has_pdf=drawing_has_pdf,
                    phase="complete",
                )

        result_payload = {
            "context": context,
            "toolCalls": safe_tool_calls,
            "nativeToolCalling": native_meta,
            "directAnswer": direct_answer,
            "skipRag": skip_rag,
            "webSources": web_sources,
            "webSearchPayload": web_search_payload,
            "selectedExternalAction": selected_external_action_meta,
            "currentMessage": raw_message,
        }

        from app.application.services.chat_drawing_turn_enrichment_service import (
            ChatDrawingTurnEnrichmentService,
        )

        result_payload = ChatDrawingTurnEnrichmentService.enrich_tool_context(
            result_payload,
            message=raw_message,
            attachment_ids=attachment_ids,
        )
        direct_answer = str(result_payload.get("directAnswer") or "").strip() or direct_answer

        if result_payload.get("drawingAnalysisMode"):
            if drawing_pdf_extract:
                result_payload[
                    "drawingPdfExtractSummary"
                ] = host._auxiliary_service._build_drawing_pdf_extract_summary(
                    drawing_pdf_extract,
                    product_code_source=drawing_product_code_source,
                )

                if drawing_pdf_extract.get("documentVision"):
                    result_payload["documentVision"] = drawing_pdf_extract["documentVision"]

            if drawing_analysis_payload:
                if not result_payload.get("drawingAnalysis") and drawing_analysis_payload.get(
                    "drawingAnalysis"
                ):
                    result_payload["drawingAnalysis"] = drawing_analysis_payload["drawingAnalysis"]

                if not result_payload.get("drawingAnalysisExport") and drawing_analysis_payload.get(
                    "drawingAnalysisExport"
                ):
                    result_payload["drawingAnalysisExport"] = drawing_analysis_payload[
                        "drawingAnalysisExport"
                    ]

        result_payload["directAnswer"] = (
            str(result_payload.get("directAnswer") or "").strip() or direct_answer
        )

        from app.application.services.chat_document_vision_turn_service import (
            ChatDocumentVisionTurnService,
        )
        from app.domain.services.chat_attachment_document_intent_service import (
            ChatAttachmentDocumentIntentService,
        )

        workspace = getattr(host, "_build_workspace_context", None) or {}
        has_agent = bool(workspace.get("agent")) if isinstance(workspace, dict) else False
        intent_route = (
            "attachment_document"
            if attachment_ids
            and ChatAttachmentDocumentIntentService.is_document_content_question(raw_message)
            else None
        )

        if attachment_ids and not result_payload.get("documentVision"):
            attachment_vision, _activation = (
                ChatDocumentVisionTurnService.run_attachment_vision_with_progress(
                    user_id=str(user_id) if user_id else None,
                    session_id=session_id,
                    attachment_ids=attachment_ids,
                    skills=drawing_runtime_skills,
                    intent_route=intent_route,
                    has_agent=has_agent,
                    on_stream_activity=on_stream_activity
                    if not drawing_analysis_mode
                    else None,
                    message=raw_message,
                )
            )

            if attachment_vision:
                result_payload["documentVision"] = attachment_vision

        return host._finalize_tool_context_result(
            message=raw_message,
            previous_messages=previous_messages,
            result=result_payload,
        )
