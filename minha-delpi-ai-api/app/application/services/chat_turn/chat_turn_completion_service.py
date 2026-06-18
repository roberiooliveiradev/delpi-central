"""Conclusão compartilhada do turno (pós-LLM) — send e stream."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_admin_debug_service import ChatAdminDebugService
from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)
from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
if TYPE_CHECKING:
    from app.application.services.chat_turn.chat_turn_preparation_service import (
        ChatTurnPreparationResult,
    )
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_message_delivery_service import ChatMessageDeliveryService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.llm.llm_request_context import get_active_config


@dataclass(frozen=True)
class ChatTurnCompletionInput:
    request: SendChatMessageRequest
    message: str
    user_id: UUID
    session_id: UUID
    workspace_context: dict
    attachments: list
    previous_messages: list
    history_source: list | None
    prepared: Any
    answer: str
    sources: list
    tool_context: dict
    tool_calls: list
    direct_answer: str | None
    pipeline_timings: ChatPipelineTimings
    pipeline_stages: list
    fast_path: bool
    operational_optimize: bool
    skip_rag: bool
    analysis_mode: bool
    llm_messages: list
    admin_debug_payload: dict | None
    active_guidelines: list
    started_at: float
    user_message: Any
    canvas_open_payload: Any | None = None


@dataclass(frozen=True)
class ChatTurnPersistenceOptions:
    mode: Literal["send", "stream_create", "stream_update"]
    is_stream: bool = False
    persist_before_playback: bool = False
    assistant_placeholder: Any | None = None


@dataclass(frozen=True)
class _FinalizeAnswerResult:
    answer: str
    canvas_open_payload: Any | None
    tool_calls: list
    email_guard_meta: Any
    correction_guard_meta: Any
    correction_canvas_updated: bool
    text_canvas_updated: bool


@dataclass(frozen=True)
class ChatTurnCompletionResult:
    answer: str
    assistant_metadata: dict
    assistant_message: Any
    canvas_open_payload: Any | None
    client_admin_debug: dict | None
    tool_calls: list
    sources: list


class ChatTurnCompletionService:
    """Persistência, metadata e auditoria pós-LLM — paridade send/stream."""

    def __init__(
        self,
        *,
        chat_repository: ChatSessionRepositoryPort,
        audit_repository: AuditRepositoryPort,
        session_memory_service=None,
    ):
        self.chat_repository = chat_repository
        self.audit_repository = audit_repository
        self.session_memory_service = session_memory_service

    def complete_turn(
        self,
        turn: ChatTurnCompletionInput,
        *,
        persistence: ChatTurnPersistenceOptions,
    ) -> ChatTurnCompletionResult:
        history = turn.history_source or turn.previous_messages
        finalized = self._finalize_answer(turn)

        intelligence_metadata, latency_ms, token_metrics = self._build_intelligence_block(
            turn,
            answer=finalized.answer,
            tool_calls=finalized.tool_calls,
        )

        answer, assistant_metadata = self._build_assistant_metadata(
            turn,
            finalized=finalized,
            intelligence_metadata=intelligence_metadata,
            latency_ms=latency_ms,
            token_metrics=token_metrics,
            history=history,
            is_stream=persistence.is_stream,
            persist_before_playback=persistence.persist_before_playback,
        )

        assistant_message = self._persist_assistant_message(
            turn,
            answer=answer,
            assistant_metadata=assistant_metadata,
            persistence=persistence,
        )

        self._patch_user_message_attachment_snapshots(turn)

        self._persist_session_memory(turn, assistant_message, assistant_metadata)
        self._set_active_leaf(turn, assistant_message)
        self._write_audit(
            turn,
            assistant_metadata=assistant_metadata,
            intelligence_metadata=intelligence_metadata,
            tool_calls=finalized.tool_calls,
            latency_ms=latency_ms,
            token_metrics=token_metrics,
            is_stream=persistence.is_stream,
        )

        client_admin_debug = ChatAdminDebugService.resolve_client_admin_debug(
            turn.request,
            build_payload=turn.admin_debug_payload,
            assistant_metadata=assistant_metadata,
        )

        return ChatTurnCompletionResult(
            answer=answer,
            assistant_metadata=assistant_metadata,
            assistant_message=assistant_message,
            canvas_open_payload=finalized.canvas_open_payload,
            client_admin_debug=client_admin_debug,
            tool_calls=finalized.tool_calls,
            sources=turn.sources,
        )

    def _patch_user_message_attachment_snapshots(self, turn: ChatTurnCompletionInput) -> None:
        if not turn.user_message or not turn.attachments:
            return

        from app.application.services.chat_attachment_preview_service import (
            ChatAttachmentPreviewService,
        )

        merged = ChatAttachmentPreviewService.merge_tool_context_vision_into_attachments(
            turn.attachments,
            turn.tool_context if isinstance(turn.tool_context, dict) else None,
        )
        snapshots = ChatAttachmentPreviewService.enrich_message_attachment_snapshots(merged)

        self.chat_repository.patch_message_metadata(
            turn.user_message.id,
            {"attachments": snapshots},
        )

    def _finalize_answer(
        self,
        turn: ChatTurnCompletionInput,
    ) -> _FinalizeAnswerResult:
        from app.application.services.chat_email_turn_service import ChatEmailTurnService
        from app.application.services.chat_text_correction_turn_service import (
            ChatTextCorrectionTurnService,
        )
        from app.domain.services.chat_advanced_sql_specialist_service import (
            ChatAdvancedSqlSpecialistService,
        )
        from app.application.services.chat_tool_context_service import ChatToolContextService

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

        answer = ChatToolContextService.resolve_authorized_persisted_answer(
            answer,
            tool_calls,
            message=turn.message,
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
            ),
        )

        from app.application.services.chat_drawing_turn_enrichment_service import (
            ChatDrawingTurnEnrichmentService,
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

        return _FinalizeAnswerResult(
            answer=answer,
            canvas_open_payload=canvas_open_payload,
            tool_calls=tool_calls,
            email_guard_meta=email_guard_meta,
            correction_guard_meta=correction_guard_meta,
            correction_canvas_updated=correction_canvas_updated,
            text_canvas_updated=text_canvas_updated,
        )

    def _build_intelligence_block(
        self,
        turn: ChatTurnCompletionInput,
        *,
        answer: str,
        tool_calls: list,
    ) -> tuple[dict, int, dict]:
        intelligence_metadata = ChatIntelligenceMetadataService.build(
            sources=turn.sources,
            tool_context=turn.tool_context,
            embedding_cache_stats=self._embedding_cache_stats(),
            pipeline_timings=turn.pipeline_timings.to_dict(),
            rag_stats=turn.rag if isinstance(turn.rag, dict) else None,
            pipeline=ChatIntelligenceMetadataService.build_pipeline_flags(
                fast_path=turn.fast_path,
                operational_optimize=turn.operational_optimize,
                tool_context=turn.tool_context,
                skip_rag=turn.skip_rag,
                analysis_mode=turn.analysis_mode,
                stages=turn.pipeline_stages,
                direct_answer=turn.direct_answer,
            ),
        )
        latency_ms = int((time.perf_counter() - turn.started_at) * 1000)
        prompt_tokens_estimated = self._estimate_tokens_from_messages(turn.llm_messages)
        completion_tokens_estimated = self._estimate_tokens(answer)
        total_tokens_estimated = prompt_tokens_estimated + completion_tokens_estimated
        estimated_cost = self._estimate_cost(
            prompt_tokens=prompt_tokens_estimated,
            completion_tokens=completion_tokens_estimated,
        )

        return (
            intelligence_metadata,
            latency_ms,
            {
                "prompt_tokens_estimated": prompt_tokens_estimated,
                "completion_tokens_estimated": completion_tokens_estimated,
                "total_tokens_estimated": total_tokens_estimated,
                "estimated_cost": estimated_cost,
            },
        )

    def _build_assistant_metadata(
        self,
        turn: ChatTurnCompletionInput,
        *,
        finalized: _FinalizeAnswerResult,
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
            "adminGuidelines": self._guideline_metadata(turn.active_guidelines),
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
            session_memory_service=self.session_memory_service,
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

    def _persist_assistant_message(
        self,
        turn: ChatTurnCompletionInput,
        *,
        answer: str,
        assistant_metadata: dict,
        persistence: ChatTurnPersistenceOptions,
    ) -> Any:
        if persistence.mode == "stream_update" and persistence.assistant_placeholder:
            assistant_message = self.chat_repository.update_assistant_message(
                persistence.assistant_placeholder.id,
                answer,
                assistant_metadata,
            )
        else:
            assistant_message = self.chat_repository.create_message(
                session_id=turn.session_id,
                role="assistant",
                content=answer,
                parent_message_id=turn.user_message.id if turn.user_message else None,
                metadata=assistant_metadata,
            )

        if not assistant_message:
            raise RuntimeError("Falha ao persistir mensagem do assistente.")

        return assistant_message

    def _persist_session_memory(
        self,
        turn: ChatTurnCompletionInput,
        assistant_message: Any,
        assistant_metadata: dict,
    ) -> None:
        if not self.session_memory_service:
            return

        post_snapshot = assistant_metadata.get("contextSnapshot")

        if isinstance(post_snapshot, dict):
            self.session_memory_service.persist_post_turn(
                session_id=turn.session_id,
                snapshot=post_snapshot,
                source_message_id=assistant_message.id,
            )

    def _set_active_leaf(self, turn: ChatTurnCompletionInput, assistant_message: Any) -> None:
        self.chat_repository.set_active_leaf_message_id(
            session_id=turn.session_id,
            user_id=turn.user_id,
            message_id=assistant_message.id,
        )

    def _write_audit(
        self,
        turn: ChatTurnCompletionInput,
        *,
        assistant_metadata: dict,
        intelligence_metadata: dict,
        tool_calls: list,
        latency_ms: int,
        token_metrics: dict,
        is_stream: bool,
    ) -> None:
        from app.application.services.chat_drawing_metrics_service import (
            ChatDrawingMetricsService,
        )
        from app.application.services.chat_document_vision_metrics_service import (
            ChatDocumentVisionMetricsService,
        )
        from app.domain.services.chat_advanced_sql_metrics_service import (
            ChatAdvancedSqlMetricsService,
        )
        from app.domain.services.chat_intent_router_metrics_service import (
            ChatIntentRouterMetricsService,
        )
        from app.domain.services.chat_text_task_admin_metrics_service import (
            ChatTextTaskAdminMetricsService,
        )
        from app.domain.services.chat_session_memory_admin_metrics_service import (
            ChatSessionMemoryAdminMetricsService,
        )
        from app.domain.services.chat_interactivity_admin_metrics_service import (
            ChatInteractivityAdminMetricsService,
        )
        from app.domain.services.chat_presentation_admin_metrics_service import (
            ChatPresentationAdminMetricsService,
        )
        from app.domain.services.chat_error_handling_admin_metrics_service import (
            ChatErrorHandlingAdminMetricsService,
        )
        from app.domain.services.chat_typing_correction_admin_metrics_service import (
            ChatTypingCorrectionAdminMetricsService,
        )
        from app.domain.services.chat_web_search_admin_metrics_service import (
            ChatWebSearchAdminMetricsService,
        )

        audit_metadata = {
            "session_id": str(turn.session_id),
            **ChatLlmMetadataService.build_assistant_llm_fields(),
            "agentId": turn.workspace_context.get("agentId"),
            "agent": turn.workspace_context.get("agent"),
            "project": turn.workspace_context.get("project"),
            "attachments": turn.attachments,
            "sources": turn.sources,
            "rag_enabled": True,
            "tool_count": len(tool_calls),
            "admin_guideline_count": len(turn.active_guidelines),
            "admin_guidelines": self._guideline_metadata(turn.active_guidelines),
            "latency_ms": latency_ms,
            "prompt_tokens_estimated": token_metrics["prompt_tokens_estimated"],
            "completion_tokens_estimated": token_metrics["completion_tokens_estimated"],
            "total_tokens_estimated": token_metrics["total_tokens_estimated"],
            "estimated_cost": token_metrics["estimated_cost"],
        }

        ChatDrawingMetricsService.enrich_audit_metadata(
            audit_metadata,
            intelligence=intelligence_metadata,
            tool_context=turn.tool_context,
            latency_ms=latency_ms,
        )
        ChatDocumentVisionMetricsService.enrich_audit_metadata(
            audit_metadata,
            intelligence=intelligence_metadata,
            tool_context=turn.tool_context,
        )
        ChatAdvancedSqlMetricsService.enrich_audit_metadata(
            audit_metadata,
            assistant_metadata=assistant_metadata,
            tool_context=turn.tool_context,
        )
        ChatIntentRouterMetricsService.enrich_audit_metadata(
            audit_metadata,
            route=turn.prepared.intent_route,
        )
        ChatTextTaskAdminMetricsService.enrich_audit_metadata(
            audit_metadata,
            assistant_metadata=assistant_metadata,
        )
        ChatSessionMemoryAdminMetricsService.enrich_audit_metadata(
            audit_metadata,
            assistant_metadata=assistant_metadata,
        )
        ChatInteractivityAdminMetricsService.enrich_audit_metadata(
            audit_metadata,
            assistant_metadata=assistant_metadata,
        )
        ChatPresentationAdminMetricsService.enrich_audit_metadata(
            audit_metadata,
            assistant_metadata=assistant_metadata,
        )
        ChatErrorHandlingAdminMetricsService.enrich_audit_metadata(
            audit_metadata,
            assistant_metadata=assistant_metadata,
        )
        ChatWebSearchAdminMetricsService.enrich_audit_metadata(
            audit_metadata,
            assistant_metadata=assistant_metadata,
        )
        ChatTypingCorrectionAdminMetricsService.enrich_audit_metadata(
            audit_metadata,
            typing_correction=turn.request.typing_correction,
        )
        ChatWebSearchAdminMetricsService.log_security_events_if_needed(
            self.audit_repository,
            user_id=turn.user_id,
            message=turn.message,
        )

        self.audit_repository.log(
            user_id=turn.user_id,
            action="chat.message.streamed" if is_stream else "chat.message.sent",
            prompt_hash=self._hash_prompt(turn.message),
            context=turn.request.context,
            tool_calls=tool_calls,
            metadata=audit_metadata,
        )

        for tool_call in tool_calls or []:
            if not isinstance(tool_call, dict):
                continue

            attempt = (tool_call.get("metadata") or {}).get("errorRecoveryAttempt")

            if isinstance(attempt, dict):
                self.audit_repository.log(
                    user_id=turn.user_id,
                    action="chat.error_recovery.attempted",
                    metadata=attempt,
                )
                break

    @staticmethod
    def _guideline_metadata(guidelines: list[dict]) -> list[dict]:
        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "status": item.get("status"),
            }
            for item in guidelines
        ]

    @staticmethod
    def _embedding_cache_stats() -> dict | None:
        try:
            from app.composition.external_action_composer import get_embedding_cache_stats

            return get_embedding_cache_stats()
        except Exception:
            return None

    def _estimate_cost(self, *, prompt_tokens: int, completion_tokens: int) -> float | None:
        try:
            from app.application.services.llm_cost_estimator_service import (
                LlmCostEstimatorService,
            )

            active = get_active_config()

            return LlmCostEstimatorService().estimate_cost(
                provider=Settings.LLM_PROVIDER,
                model=active.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        except Exception:
            return None

    def _estimate_tokens_from_messages(self, messages: list[dict]) -> int:
        total = 0

        for item in messages:
            if isinstance(item, dict):
                total += self._estimate_tokens(str(item.get("content") or ""))

        return total

    @staticmethod
    def _estimate_tokens(value: str) -> int:
        normalized = str(value or "").strip()

        if not normalized:
            return 0

        return max(1, round(len(normalized) / 4))

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
