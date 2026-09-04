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

        from app.domain.services.chat_meta_llm_synthesis_service import (
            ChatMetaLlmSynthesisService,
        )

        if isinstance(turn.tool_context, dict) and turn.tool_context.get(
            ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_LLM_SYNTHESIS
        ):
            answer = ChatMetaLlmSynthesisService.guard_delivered_answer(
                answer=answer,
                tool_context=turn.tool_context,
            )

        answer = cls._guard_free_path_llm_synthesis_leak(
            answer=answer,
            tool_context=turn.tool_context if isinstance(turn.tool_context, dict) else None,
            tool_calls=tool_calls,
            message=turn.message,
            workspace_context=turn.workspace_context,
            previous_messages=turn.previous_messages,
        )
        answer = cls._maybe_prepend_revise_ack(
            answer,
            workspace_context=turn.workspace_context,
            tool_context=turn.tool_context if isinstance(turn.tool_context, dict) else None,
        ) or answer

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

    @classmethod
    def _guard_free_path_llm_synthesis_leak(
        cls,
        *,
        answer: str,
        tool_context: dict | None,
        tool_calls: list,
        message: str | None = None,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> str:
        """Aplica a guarda CoT/EN no caminho livre (sem tools) e em llm_synthesis*."""
        from app.domain.services.chat_llm_synthesis_delivery_content_service import (
            ChatLlmSynthesisDeliveryContentService,
        )
        from app.domain.services.chat_llm_synthesis_leak_guard_service import (
            ChatLlmSynthesisLeakGuardService,
        )
        from app.domain.services.chat_operational_narrative_synthesis_service import (
            ChatOperationalNarrativeSynthesisService,
        )

        context = tool_context if isinstance(tool_context, dict) else {}
        effect = str(context.get("responseModeEffect") or "").strip()
        has_tools = bool(tool_calls)
        is_synthesis = ChatOperationalNarrativeSynthesisService.is_llm_synthesis_effect(effect)

        from app.domain.services.chat_llm_generation_context_service import (
            consume_reasoning_fallback,
        )

        reasoning_fallback = bool(context.get("reasoningFallback")) or consume_reasoning_fallback()

        if has_tools and is_synthesis and not reasoning_fallback:
            # Operacional com tools já guarda em ChatOperationalLlmSynthesisTurnFinalizationService.
            return answer

        # RAG/tools sem síntese operacional também vazam CoT EN no content — sempre guardar.
        guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
            answer=answer,
            fallback=ChatLlmSynthesisDeliveryContentService.safe_fallback_answer(),
        )

        if (
            guarded == ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
            and context.get("groundedNarrate")
        ):
            from app.application.services.chat_grounded_narrate_answer_service import (
                ChatGroundedNarrateAnswerService,
            )
            from app.application.services.chat_follow_up_grounded_answer_service import (
                ChatFollowUpGroundedAnswerService,
            )

            if context.get("followUpChallenge"):
                challenge = ChatFollowUpGroundedAnswerService.build_challenge_answer(
                    workspace_context=workspace_context,
                    tool_context=context,
                    previous_messages=previous_messages,
                )
                if challenge:
                    return challenge

            template = ChatGroundedNarrateAnswerService.build_answer(
                str(message or context.get("currentMessage") or ""),
                previous_messages,
                workspace_context=workspace_context,
                tool_context=context,
            )

            if template:
                return template

        return guarded

    @classmethod
    def _maybe_prepend_revise_ack(
        cls,
        answer: str,
        *,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> str | None:
        from app.application.services.chat_follow_up_grounded_answer_service import (
            ChatFollowUpGroundedAnswerService,
        )

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        context = tool_context if isinstance(tool_context, dict) else {}
        turn = context.get("turnGrounding") or workspace.get("turnGrounding") or {}
        if not isinstance(turn, dict):
            return None
        if str(turn.get("stage") or "").strip() != "grounded_revise_query":
            return None

        tool_calls = context.get("toolCalls") or []
        compare = ChatFollowUpGroundedAnswerService.build_period_compare_answer(
            tool_calls=tool_calls if isinstance(tool_calls, list) else None,
            workspace_context=workspace,
        )
        if compare:
            suggestions = context.get("followUpSuggestions")
            if not suggestions and isinstance(workspace.get("followUpSuggestions"), list):
                context["followUpSuggestions"] = workspace.get("followUpSuggestions")
            return compare

        params: dict = {}
        baseline_params: dict = {}
        follow_up = turn.get("followUp") if isinstance(turn.get("followUp"), dict) else {}
        slot_delta = (
            follow_up.get("slotDelta") if isinstance(follow_up.get("slotDelta"), dict) else {}
        )
        if slot_delta.get("baseline_start_date") and slot_delta.get("baseline_end_date"):
            baseline_params = {
                "start_date": slot_delta.get("baseline_start_date"),
                "end_date": slot_delta.get("baseline_end_date"),
            }

        for tool_call in reversed(tool_calls if isinstance(tool_calls, list) else []):
            if not isinstance(tool_call, dict):
                continue
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue
            args = tool_call.get("arguments")
            if isinstance(args, dict) and isinstance(args.get("parameters"), dict):
                params = dict(args.get("parameters") or {})
                break

        if not baseline_params and slot_delta.get("period") == "message_resolved":
            # «deste mês» vs lastAction herdado — marcar período como alterado.
            last_action = None
            working = workspace.get("workingMemory")
            if isinstance(working, dict):
                last_action = working.get("lastAction")
            if isinstance(last_action, dict) and isinstance(last_action.get("params"), dict):
                baseline_params = {
                    "start_date": last_action["params"].get("start_date"),
                    "end_date": last_action["params"].get("end_date"),
                }

        ack = ChatFollowUpGroundedAnswerService.build_revise_ack(
            parameters=params,
            baseline_parameters=baseline_params or None,
        )
        if not ack:
            return None
        text = str(answer or "").strip()
        if not text:
            return ack
        if ack.lower() in text.lower():
            return text
        return f"{ack}\n\n{text}"
