"""Metadata do assistente pós-LLM — anexos transversais ao turno."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_admin_debug_service import ChatAdminDebugService
from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.application.services.chat_turn.chat_turn_completion_models import (
    ChatTurnCompletionFinalizeResult,
    ChatTurnCompletionInput,
)
from app.domain.services.chat_message_delivery_service import ChatMessageDeliveryService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatTurnCompletionMetadataService:
    @classmethod
    def build(
        cls,
        turn: ChatTurnCompletionInput,
        *,
        session_memory_service,
        finalized: ChatTurnCompletionFinalizeResult,
        intelligence_metadata: dict,
        latency_ms: int,
        token_metrics: dict,
        history: list,
        is_stream: bool,
        persist_before_playback: bool,
    ) -> tuple[str, dict]:
        answer = finalized.answer
        tool_calls = finalized.tool_calls
        canvas_open_payload = finalized.canvas_open_payload
        assistant_metadata: dict[str, Any] = {
            **ChatLlmMetadataService.build_assistant_llm_fields(),
            "agentId": turn.workspace_context.get("agentId"),
            "agent": turn.workspace_context.get("agent"),
            "project": turn.workspace_context.get("project"),
            "attachments": turn.attachments,
            "sources": turn.sources,
            "toolCalls": tool_calls,
            "rag": {
                "enabled": True,
                "sourceCount": len(turn.sources),
            },
            "intelligence": intelligence_metadata,
            "adminGuidelines": ChatTurnCompletionMetadataService.guideline_metadata(
                turn.active_guidelines
            ),
            "metrics": {
                "latencyMs": latency_ms,
                "promptTokensEstimated": token_metrics["prompt_tokens_estimated"],
                "completionTokensEstimated": token_metrics["completion_tokens_estimated"],
                "totalTokensEstimated": token_metrics["total_tokens_estimated"],
                "estimatedCost": token_metrics["estimated_cost"],
            },
            "directResponse": bool(turn.direct_answer),
        }

        if is_stream:
            assistant_metadata["stream"] = True

        ChatAdminDebugService.attach_to_assistant_metadata(
            assistant_metadata,
            turn.admin_debug_payload,
            intelligence_metadata=intelligence_metadata,
        )

        from app.domain.services.chat_intent_router_metrics_service import (
            ChatIntentRouterMetricsService,
        )

        ChatIntentRouterMetricsService.attach_to_assistant_metadata(
            assistant_metadata,
            turn.prepared.intent_route,
            normalized_message=turn.request.message,
        )

        from app.application.services.chat_intent_disambiguation_follow_up_service import (
            ChatIntentDisambiguationFollowUpService,
        )

        ChatIntentDisambiguationFollowUpService.attach_to_assistant_metadata(
            assistant_metadata,
            suggestions=turn.prepared.routing_disambiguation_suggestions,
        )

        from app.application.services.chat_active_pending_service import (
            ChatActivePendingService,
        )

        ChatActivePendingService.attach_for_operational_direct_answer(
            assistant_metadata,
            message=turn.request.message,
            previous_messages=turn.previous_messages,
            pipeline_stages=turn.pipeline_stages,
        )

        from app.domain.services.chat_active_query_session_service import (
            ChatActiveQuerySessionService,
        )

        ChatActiveQuerySessionService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.request.message,
            tool_context=turn.tool_context,
            pipeline_stages=turn.pipeline_stages,
            previous_messages=turn.previous_messages,
        )

        from app.application.services.chat_web_search_research_activity_service import (
            ChatWebSearchResearchActivityService,
        )

        ChatWebSearchResearchActivityService.attach_to_assistant_metadata(
            assistant_metadata,
            tool_context=turn.tool_context,
            pipeline_stages=turn.pipeline_stages,
            latency_ms=latency_ms,
        )

        from app.application.services.chat_web_search_follow_up_service import (
            ChatWebSearchFollowUpService,
        )

        ChatWebSearchFollowUpService.attach_to_assistant_metadata(
            assistant_metadata,
            tool_context=turn.tool_context,
            message=turn.request.message,
            had_attachments=bool(getattr(turn.request, "attachment_ids", None)),
        )

        from app.application.services.chat_help_follow_up_service import (
            ChatHelpFollowUpService,
        )

        ChatHelpFollowUpService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.request.message,
        )

        from app.application.services.chat_help_self_help_telemetry_service import (
            ChatHelpSelfHelpTelemetryService,
        )

        ChatHelpSelfHelpTelemetryService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.request.message,
            workspace_context=turn.workspace_context,
            had_direct_answer=bool(turn.direct_answer),
        )

        from app.application.services.chat_onboarding_follow_up_service import (
            ChatOnboardingFollowUpService,
        )

        ChatOnboardingFollowUpService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.request.message,
            pipeline_stages=turn.pipeline_stages,
        )

        from app.application.services.chat_onboarding_milestone_service import (
            ChatOnboardingMilestoneService,
        )

        ChatOnboardingMilestoneService.attach_to_assistant_metadata(
            assistant_metadata,
            previous_messages=history,
            pipeline_stages=turn.pipeline_stages,
            tool_calls=tool_calls,
            had_attachments=bool(getattr(turn.request, "attachment_ids", None)),
            canvas_open=bool(canvas_open_payload),
        )

        from app.application.services.chat_guided_flow_service import (
            ChatGuidedFlowService,
        )

        ChatGuidedFlowService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.request.message,
            workspace_context=turn.workspace_context,
        )

        if canvas_open_payload:
            assistant_metadata["canvasOpen"] = {
                "title": canvas_open_payload.title,
                "markdown": canvas_open_payload.markdown,
                "sourceMessageId": canvas_open_payload.source_message_id,
            }

            from app.application.services.chat_canvas_session_metadata_service import (
                ChatCanvasSessionMetadataService,
            )
            from app.domain.services.chat_canvas_intent_service import (
                ChatCanvasIntentService,
            )

            operation = "open"

            if ChatCanvasIntentService.is_canvas_transform_request(turn.request.message):
                operation = "transform"
            elif ChatCanvasIntentService.is_canvas_update_request(turn.request.message):
                operation = "append"

            normalized_canvas = ChatMessageNormalizationService.normalize_for_matching(
                turn.request.message
            )

            if any(token in normalized_canvas for token in ("substitu", "substitua", "trocar")):
                operation = "replace"

            ChatCanvasSessionMetadataService.attach_open(
                assistant_metadata,
                open_payload=canvas_open_payload,
                operation=operation,
                previous_messages=history,
            )

            from app.application.services.chat_attachment_artifact_telemetry_service import (
                ChatAttachmentArtifactTelemetryService,
            )

            ChatAttachmentArtifactTelemetryService.attach_canvas_open(
                assistant_metadata,
                operation=operation,
            )

        from app.application.services.chat_personality_metadata_service import (
            ChatPersonalityMetadataService,
        )

        ChatPersonalityMetadataService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.message,
            answer=answer,
            tool_calls=tool_calls,
            workspace_context=turn.workspace_context,
            previous_messages=history,
            issues=intelligence_metadata.get("issues")
            if isinstance(intelligence_metadata, dict)
            else None,
            attachments=turn.attachments,
            latency_ms=latency_ms,
        )

        from app.application.services.chat_error_handling_telemetry_service import (
            ChatErrorHandlingTelemetryService,
        )

        ChatErrorHandlingTelemetryService.log_classification(assistant_metadata)

        from app.application.services.chat_error_handling_service import (
            ChatErrorHandlingService,
        )

        answer = ChatErrorHandlingService.resolve_display_answer(answer, assistant_metadata)

        from app.application.services.chat_context_metadata_service import (
            ChatContextMetadataService,
        )

        ChatContextMetadataService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.message,
            answer=answer,
            tool_calls=tool_calls,
            previous_messages=history,
            workspace_context=turn.workspace_context,
            session_memory_service=session_memory_service,
        )

        from app.application.services.chat_attachment_follow_up_service import (
            ChatAttachmentFollowUpService,
        )

        ChatAttachmentFollowUpService.attach_to_assistant_metadata(
            assistant_metadata,
            had_attachments=bool(getattr(turn.request, "attachment_ids", None)),
            attachments=turn.attachments,
            message=turn.message,
        )

        from app.application.services.chat_attachment_artifact_telemetry_service import (
            ChatAttachmentArtifactTelemetryService,
        )
        from app.application.services.chat_attachment_source_citation_service import (
            ChatAttachmentSourceCitationService,
        )
        from app.application.services.chat_canvas_follow_up_service import (
            ChatCanvasFollowUpService,
        )

        if bool(getattr(turn.request, "attachment_ids", None)):
            ChatAttachmentArtifactTelemetryService.attach_attachment_welcome(
                assistant_metadata,
                attachments=turn.attachments,
            )

        ChatAttachmentSourceCitationService.attach_to_assistant_metadata(
            assistant_metadata,
            attachments=turn.attachments,
            answer=answer,
        )

        ChatCanvasFollowUpService.attach_to_assistant_metadata(
            assistant_metadata,
            workspace_context=turn.workspace_context,
            previous_messages=history,
            opened_canvas_this_turn=bool(canvas_open_payload),
        )

        from app.application.services.chat_drawing_follow_up_service import (
            ChatDrawingFollowUpService,
        )
        from app.application.services.chat_email_turn_service import ChatEmailTurnService
        from app.application.services.chat_text_correction_turn_service import (
            ChatTextCorrectionTurnService,
        )

        ChatDrawingFollowUpService.attach_to_assistant_metadata(
            assistant_metadata,
            intelligence=intelligence_metadata,
            tool_context=turn.tool_context,
            latency_ms=latency_ms,
        )

        ChatEmailTurnService.attach_follow_up_metadata(
            assistant_metadata,
            message=turn.message,
            answer=answer,
            workspace_context=turn.workspace_context,
            tool_context=turn.tool_context,
            guard_meta=finalized.email_guard_meta,
        )

        ChatTextCorrectionTurnService.attach_follow_up_metadata(
            assistant_metadata,
            message=turn.message,
            answer=answer,
            workspace_context=turn.workspace_context,
            guard_meta=finalized.correction_guard_meta,
            canvas_updated=finalized.correction_canvas_updated,
        )

        if turn.prepared.text_task_mode:
            from app.application.services.chat_text_task_turn_service import (
                ChatTextTaskTurnService,
            )

            ChatTextTaskTurnService.attach_follow_up_metadata(
                assistant_metadata,
                message=turn.message,
                answer=answer,
                workspace_context=turn.workspace_context,
                text_task_mode=True,
                correction_guard_meta=finalized.correction_guard_meta,
                canvas_updated=(
                    finalized.correction_canvas_updated or finalized.text_canvas_updated
                ),
                pipeline_stages=turn.pipeline_stages,
                tool_context=turn.tool_context,
                canvas_title=canvas_open_payload.title if canvas_open_payload else None,
                canvas_markdown=canvas_open_payload.markdown if canvas_open_payload else None,
                previous_messages=turn.previous_messages,
            )

        from app.application.services.chat_document_vision_metrics_service import (
            ChatDocumentVisionMetricsService,
        )

        ChatDocumentVisionMetricsService.attach_to_assistant_metadata(
            assistant_metadata,
            intelligence=intelligence_metadata,
            tool_context=turn.tool_context,
        )

        from app.domain.services.chat_advanced_sql_specialist_service import (
            ChatAdvancedSqlSpecialistService,
        )
        from app.domain.services.chat_advanced_sql_metrics_service import (
            ChatAdvancedSqlMetricsService,
        )

        ChatAdvancedSqlSpecialistService.attach_to_assistant_metadata(
            assistant_metadata,
            message=turn.message,
            workspace_context=turn.workspace_context,
            previous_messages=turn.previous_messages,
            tool_calls=tool_calls,
        )
        ChatAdvancedSqlMetricsService.attach_to_assistant_metadata(
            assistant_metadata,
            tool_context=turn.tool_context,
        )

        from app.application.services.chat_interactivity_suggestion_service import (
            ChatInteractivitySuggestionService,
        )
        from app.application.services.chat_interactivity_telemetry_service import (
            ChatInteractivityTelemetryService,
        )

        intent_route = assistant_metadata.get("intentRouting")

        ChatInteractivitySuggestionService.attach_to_assistant_metadata(
            assistant_metadata,
            workspace_context=turn.workspace_context,
            tool_calls=tool_calls,
            intent_route=intent_route if isinstance(intent_route, dict) else None,
            message=turn.message,
        )
        ChatInteractivityTelemetryService.log_from_metadata(assistant_metadata)

        from app.domain.services.chat_response_metadata_service import (
            ChatResponseMetadataService,
        )

        ChatResponseMetadataService.attach_to_assistant_metadata(
            assistant_metadata,
            workspace_context=turn.workspace_context,
            session_id=str(turn.session_id),
            duration_ms=latency_ms,
        )

        if persist_before_playback:
            assistant_metadata = ChatMessageDeliveryService.ready_metadata(
                assistant_metadata,
                playback_pending=True,
            )

        return answer, assistant_metadata

    @staticmethod
    def guideline_metadata(guidelines: list[dict]) -> list[dict]:
        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "status": item.get("status"),
            }
            for item in guidelines
        ]

