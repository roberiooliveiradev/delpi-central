"""Recupera mensagens presas quando o produtor SSE falha em segundo plano."""

from __future__ import annotations

from uuid import UUID

from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_delivery_service import ChatMessageDeliveryService


_IN_FLIGHT_USER_STATUSES = frozenset({"submitted", "processing"})


class ChatStreamFailureRecoveryService:
    @classmethod
    def recover(
        cls,
        *,
        chat_repository: ChatSessionRepositoryPort,
        session_id: UUID | str | None,
        detail: str | None = None,
    ) -> None:
        if not session_id:
            return

        parsed_session_id = UUID(str(session_id))
        session = chat_repository.get_session_by_id(parsed_session_id)

        if not session:
            return

        messages = chat_repository.list_messages_by_session(parsed_session_id)

        if not messages:
            return

        error_text = (
            ChatAssistantContentService.get("stream", "errorGenericStatus")
            or "Não foi possível concluir a resposta agora. Tente novamente."
        )
        if detail:
            error_text = f"{error_text} ({detail[:180]})"

        last = messages[-1]
        last_metadata = dict(last.metadata or {})
        delivery_status = ChatMessageDeliveryService.get_status(last_metadata)

        if last.role == "assistant" and ChatMessageDeliveryService.is_generating(
            last_metadata
        ):
            chat_repository.update_assistant_message(
                last.id,
                error_text,
                ChatMessageDeliveryService.ready_metadata(
                    last_metadata,
                    playback_pending=False,
                ),
            )
            return

        if last.role == "user" and delivery_status in _IN_FLIGHT_USER_STATUSES:
            chat_repository.update_user_message(
                last.id,
                session.user_id,
                last.content,
                metadata_patch={
                    "delivery": {
                        **dict(last_metadata.get("delivery") or {}),
                        "status": "cancelled",
                        "playbackPending": False,
                        "error": detail[:300] if detail else None,
                    }
                },
            )
