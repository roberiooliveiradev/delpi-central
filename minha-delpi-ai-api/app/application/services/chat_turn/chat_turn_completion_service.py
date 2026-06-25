"""Conclusão compartilhada do turno (pós-LLM) — send e stream."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_admin_debug_service import ChatAdminDebugService
from app.application.services.chat_turn.chat_turn_completion_audit_service import (
    ChatTurnCompletionAuditService,
)
from app.application.services.chat_turn.chat_turn_completion_finalize_service import (
    ChatTurnCompletionFinalizeService,
)
from app.application.services.chat_turn.chat_turn_completion_intelligence_service import (
    ChatTurnCompletionIntelligenceService,
)
from app.application.services.chat_turn.chat_turn_completion_metadata_service import (
    ChatTurnCompletionMetadataService,
)
from app.application.services.chat_turn.chat_turn_completion_models import (
    ChatTurnCompletionInput,
    ChatTurnCompletionResult,
    ChatTurnPersistenceOptions,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort

# Re-export para compatibilidade com use cases e testes existentes.
__all__ = [
    "ChatTurnCompletionInput",
    "ChatTurnCompletionResult",
    "ChatTurnCompletionService",
    "ChatTurnPersistenceOptions",
]


class ChatTurnCompletionService:
    """Orquestra delegates pós-LLM — paridade send/stream."""

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
        finalized = ChatTurnCompletionFinalizeService.finalize(turn)

        intelligence_metadata, latency_ms, token_metrics = (
            ChatTurnCompletionIntelligenceService.build_block(
                turn,
                answer=finalized.answer,
                tool_calls=finalized.tool_calls,
            )
        )

        answer, assistant_metadata = ChatTurnCompletionMetadataService.build(
            turn,
            session_memory_service=self.session_memory_service,
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

        ChatTurnCompletionAuditService.write(
            self.audit_repository,
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

        if not getattr(turn.request, "attachment_ids", None):
            from app.application.services.chat_drawing_library_attachment_service import (
                ChatDrawingLibraryAttachmentService,
            )

            if (
                ChatDrawingLibraryAttachmentService.attachments_are_library_only(
                    turn.attachments
                )
                or ChatDrawingLibraryAttachmentService.is_library_only_drawing_turn(
                    tool_context=turn.tool_context,
                    request_attachment_ids=getattr(turn.request, "attachment_ids", None),
                )
            ):
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

    @staticmethod
    def _estimate_cost(*, prompt_tokens: int, completion_tokens: int) -> float | None:
        """Compatibilidade com mocks de teste — delega ao serviço de inteligência."""
        return ChatTurnCompletionIntelligenceService.estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
