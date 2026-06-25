"""Finalização da resposta pós-LLM — guards, SQL, canvas e prosa autorizada."""

from __future__ import annotations

from app.application.services.chat_turn.chat_turn_completion_models import (
    ChatTurnCompletionFinalizeResult,
    ChatTurnCompletionInput,
)


class ChatTurnCompletionFinalizeService:
    @classmethod
    def finalize(cls, turn: ChatTurnCompletionInput) -> ChatTurnCompletionFinalizeResult:
        from app.application.services.chat_drawing_turn_enrichment_service import (
            ChatDrawingTurnEnrichmentService,
        )
        from app.application.services.chat_email_turn_service import ChatEmailTurnService
        from app.application.services.chat_text_correction_turn_service import (
            ChatTextCorrectionTurnService,
        )
        from app.application.services.chat_tool_context_service import ChatToolContextService
        from app.domain.services.chat_advanced_sql_specialist_service import (
            ChatAdvancedSqlSpecialistService,
        )
        from app.domain.services.chat_operational_narrative_synthesis_service import (
            ChatOperationalNarrativeSynthesisService,
        )
        from app.domain.services.chat_response_mode_service import ChatResponseModeService

        answer = turn.answer
        tool_calls = list(turn.tool_calls or [])
        canvas_open_payload = turn.canvas_open_payload

        answer, email_guard_meta = ChatEmailTurnService.finalize_answer(
            answer,
            message=turn.message,
            workspace_context=turn.workspace_context,
        )
        answer, correction_guard_meta = ChatTextCorrectionTurnService.finalize_answer(
            answer,
            message=turn.message,
            workspace_context=turn.workspace_context,
        )

        sql_snapshot = (
            turn.tool_context.get("sqlAdvanced")
            if isinstance(turn.tool_context, dict)
            and isinstance(turn.tool_context.get("sqlAdvanced"), dict)
            else None
        )
        answer = ChatAdvancedSqlSpecialistService.ensure_required_sql_block(
            answer,
            snapshot=sql_snapshot,
        )
        answer = ChatAdvancedSqlSpecialistService.normalize_protheus_sql_answer(
            answer,
            message=turn.message,
            tool_calls=ChatAdvancedSqlSpecialistService.sanitize_tool_calls_for_client(
                tool_calls
            ),
        )
        answer = ChatAdvancedSqlSpecialistService.format_sql_authoring_answer(answer)
        tool_calls = ChatAdvancedSqlSpecialistService.sanitize_tool_calls_for_client(tool_calls)

        response_mode = ChatResponseModeService.normalize(
            (
                turn.tool_context.get("responseMode")
                if isinstance(turn.tool_context, dict)
                else None
            )
            or getattr(turn.request, "response_mode", None),
        )

        answer = ChatToolContextService.resolve_authorized_persisted_answer(
            answer,
            tool_calls,
            message=turn.message,
            response_mode_effect=(
                turn.tool_context.get("responseModeEffect")
                if isinstance(turn.tool_context, dict)
                else None
            ),
            response_mode=response_mode,
            skip_replacement=bool(
                turn.prepared.email_writing_mode
                or turn.prepared.text_correction_mode
                or (
                    isinstance(turn.tool_context, dict)
                    and turn.tool_context.get("sqlRequiresLlm")
                )
                or (
                    isinstance(turn.tool_context, dict)
                    and turn.tool_context.get("drawingAnalysisMode")
                    and turn.tool_context.get("drawingAnalysis")
                )
                or (
                    isinstance(turn.tool_context, dict)
                    and ChatOperationalNarrativeSynthesisService.is_llm_synthesis_effect(
                        turn.tool_context.get("responseModeEffect")
                    )
                )
            ),
        )

        drawing_report_answer = ChatDrawingTurnEnrichmentService.resolve_report_direct_answer(
            turn.tool_context if isinstance(turn.tool_context, dict) else None,
        )

        if drawing_report_answer:
            answer = drawing_report_answer

        correction_canvas_payload = (
            ChatTextCorrectionTurnService.resolve_canvas_open_after_correction(
                message=turn.message,
                answer=answer,
                previous_messages=turn.previous_messages,
                workspace_context=turn.workspace_context,
            )
        )
        correction_canvas_updated = bool(correction_canvas_payload)

        if correction_canvas_payload:
            canvas_open_payload = correction_canvas_payload
            answer = ChatTextCorrectionTurnService.apply_canvas_update_to_answer(
                answer,
                canvas_payload=correction_canvas_payload,
            )

        text_canvas_updated = False

        if turn.prepared.text_task_mode and not canvas_open_payload:
            from app.application.services.chat_text_task_canvas_service import (
                ChatTextTaskCanvasService,
            )

            text_canvas_payload = ChatTextTaskCanvasService.resolve_canvas_open_after_text_task(
                message=turn.message,
                answer=answer,
                previous_messages=turn.previous_messages,
                workspace_context=turn.workspace_context,
            )

            if text_canvas_payload:
                canvas_open_payload = text_canvas_payload
                text_canvas_updated = True
                answer = ChatTextTaskCanvasService.append_canvas_update_note(
                    answer,
                    title=text_canvas_payload.title,
                )

        turn.pipeline_timings.mark("llm_done")

        return ChatTurnCompletionFinalizeResult(
            answer=answer,
            canvas_open_payload=canvas_open_payload,
            tool_calls=tool_calls,
            email_guard_meta=email_guard_meta,
            correction_guard_meta=correction_guard_meta,
            correction_canvas_updated=correction_canvas_updated,
            text_canvas_updated=text_canvas_updated,
        )
