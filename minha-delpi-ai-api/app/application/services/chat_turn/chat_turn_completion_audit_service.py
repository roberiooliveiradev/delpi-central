"""Auditoria pós-turno — métricas admin e log de ações."""

from __future__ import annotations

import hashlib

from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.application.services.chat_turn.chat_turn_completion_metadata_service import (
    ChatTurnCompletionMetadataService,
)
from app.application.services.chat_turn.chat_turn_completion_models import (
    ChatTurnCompletionInput,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort


class ChatTurnCompletionAuditService:
    @classmethod
    def write(
        cls,
        audit_repository: AuditRepositoryPort,
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
            "admin_guidelines": ChatTurnCompletionMetadataService.guideline_metadata(
                turn.active_guidelines
            ),
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
            audit_repository,
            user_id=turn.user_id,
            message=turn.message,
        )

        audit_repository.log(
            user_id=turn.user_id,
            action="chat.message.streamed" if is_stream else "chat.message.sent",
            prompt_hash=cls.hash_prompt(turn.message),
            context=turn.request.context,
            tool_calls=tool_calls,
            metadata=audit_metadata,
        )

        for tool_call in tool_calls or []:
            if not isinstance(tool_call, dict):
                continue

            attempt = (tool_call.get("metadata") or {}).get("errorRecoveryAttempt")

            if isinstance(attempt, dict):
                audit_repository.log(
                    user_id=turn.user_id,
                    action="chat.error_recovery.attempted",
                    metadata=attempt,
                )
                break

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
