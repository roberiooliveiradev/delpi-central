"""Persistência da mensagem do usuário no stream — Fase 4B lote 2."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.application.services.chat_turn.chat_turn_use_case_support_service import (
    ChatTurnUseCaseSupportService,
)
from app.domain.exceptions.chat_exceptions import (
    ChatMessageNotFoundError,
    ChatSessionAccessDeniedError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_message_branch_service import ChatMessageBranchService


@dataclass(frozen=True)
class ChatStreamUserMessagePersistResult:
    user_message: object
    events: list[dict]


class ChatStreamUserMessageService:
    @classmethod
    def persist(
        cls,
        *,
        chat_repository: ChatSessionRepositoryPort,
        turn_support: ChatTurnUseCaseSupportService,
        request: SendChatMessageRequest,
        message: str,
        session,
        user_id: UUID,
        session_id: UUID,
        workspace_context: dict,
        attachments: list[dict],
        previous_messages: list,
        resend_from_message_id: str | None,
    ) -> ChatStreamUserMessagePersistResult:
        events: list[dict] = []

        if resend_from_message_id:
            user_message = cls._persist_resend_branch(
                chat_repository=chat_repository,
                turn_support=turn_support,
                request=request,
                message=message,
                user_id=user_id,
                session_id=session_id,
                workspace_context=workspace_context,
                attachments=attachments,
                previous_messages=previous_messages,
                resend_from_message_id=resend_from_message_id,
            )
        else:
            user_message = cls._persist_new_turn(
                chat_repository=chat_repository,
                turn_support=turn_support,
                request=request,
                message=message,
                session=session,
                user_id=user_id,
                session_id=session_id,
                workspace_context=workspace_context,
                attachments=attachments,
            )

        events.append(
            {
                "type": "user_persisted",
                "messageId": str(user_message.id),
            }
        )

        return ChatStreamUserMessagePersistResult(
            user_message=user_message,
            events=events,
        )

    @staticmethod
    def _persist_resend_branch(
        *,
        chat_repository: ChatSessionRepositoryPort,
        turn_support: ChatTurnUseCaseSupportService,
        request: SendChatMessageRequest,
        message: str,
        user_id: UUID,
        session_id: UUID,
        workspace_context: dict,
        attachments: list[dict],
        previous_messages: list,
        resend_from_message_id: str,
    ):
        anchor = chat_repository.get_user_message_for_user(
            message_id=UUID(resend_from_message_id),
            user_id=user_id,
            session_id=session_id,
        )

        if not anchor:
            raise ChatMessageNotFoundError()

        if anchor.session_id != session_id:
            raise ChatSessionAccessDeniedError()

        siblings = ChatMessageBranchService.list_user_siblings(previous_messages, anchor)

        user_message = chat_repository.create_message(
            session_id=session_id,
            role="user",
            content=message,
            parent_message_id=anchor.parent_message_id,
            metadata={
                "context": request.context,
                "agentId": workspace_context.get("agentId"),
                "agent": workspace_context.get("agent"),
                "project": workspace_context.get("project"),
                "attachments": attachments,
                "stream": True,
                "branch": {
                    "forkedFromMessageId": str(anchor.id),
                    "variantIndex": len(siblings) + 1,
                },
                **ChatLlmMetadataService.user_message_response_mode(request),
                "delivery": {"status": "submitted"},
            },
        )

        turn_support.attach_files_to_message(
            request=request,
            user_id=user_id,
            session_id=session_id,
            message_id=user_message.id,
        )

        chat_repository.set_active_leaf_message_id(
            session_id=session_id,
            user_id=user_id,
            message_id=user_message.id,
        )

        return user_message

    @staticmethod
    def _persist_new_turn(
        *,
        chat_repository: ChatSessionRepositoryPort,
        turn_support: ChatTurnUseCaseSupportService,
        request: SendChatMessageRequest,
        message: str,
        session,
        user_id: UUID,
        session_id: UUID,
        workspace_context: dict,
        attachments: list[dict],
    ):
        user_message = chat_repository.create_message(
            session_id=session_id,
            role="user",
            content=message,
            parent_message_id=session.active_leaf_message_id,
            metadata={
                "context": request.context,
                "agentId": workspace_context.get("agentId"),
                "agent": workspace_context.get("agent"),
                "project": workspace_context.get("project"),
                "attachments": attachments,
                "stream": True,
                **ChatLlmMetadataService.user_message_response_mode(request),
                "delivery": {"status": "submitted"},
            },
        )

        turn_support.attach_files_to_message(
            request=request,
            user_id=user_id,
            session_id=session_id,
            message_id=user_message.id,
        )

        chat_repository.set_active_leaf_message_id(
            session_id=session_id,
            user_id=user_id,
            message_id=user_message.id,
        )

        return user_message
