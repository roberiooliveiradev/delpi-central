"""Preparação assíncrona do turno no stream — Fase 4B lote 2."""

from __future__ import annotations

import queue
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import partial
from typing import Any
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_intelligence_runtime_access import (
    resolve_chat_intelligence_runtime,
)
from app.application.services.chat_turn.chat_stream_session_title_service import (
    ChatStreamSessionTitleService,
)
from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from app.application.services.chat_turn.chat_turn_use_case_support_service import (
    ChatTurnUseCaseSupportService,
)
from app.application.services.chat_user_context_service import ChatUserContextService
from app.domain.exceptions.chat_exceptions import (
    ChatMessageNotFoundError,
    ChatSessionAccessDeniedError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_branch_service import ChatMessageBranchService
from app.infrastructure.config.settings import Settings
from app.infrastructure.llm.llm_request_context import llm_generation_scope


@dataclass
class ChatStreamPrepareWorkerState:
    activity_queue: queue.Queue = field(default_factory=queue.Queue)
    prepared_box: dict = field(default_factory=dict)
    prepare_error_box: dict = field(default_factory=dict)
    context_box: dict = field(default_factory=dict)


class ChatStreamTurnPrepareService:
    def __init__(
        self,
        *,
        chat_repository: ChatSessionRepositoryPort,
        turn_preparation_service: ChatTurnPreparationService,
        turn_support: ChatTurnUseCaseSupportService,
        session_title_service: ChatStreamSessionTitleService | None = None,
    ) -> None:
        self.chat_repository = chat_repository
        self.turn_preparation_service = turn_preparation_service
        self.turn_support = turn_support
        self.session_title_service = session_title_service or ChatStreamSessionTitleService()

    def start_worker(
        self,
        *,
        request: SendChatMessageRequest,
        message: str,
        session,
        user_id: UUID,
        session_id: UUID,
        resend_from_message_id: str | None,
        workspace_context: dict,
        attachments: list,
        previous_messages: list,
        user_message: Any,
        turn_generation_config,
        flask_app,
    ) -> ChatStreamPrepareWorkerState:
        state = ChatStreamPrepareWorkerState(
            context_box={
                "workspace_context": workspace_context,
                "attachments": attachments,
                "previous_messages": previous_messages,
                "user_message": user_message,
            }
        )
        suppress_activity = {"value": False}

        def _on_stream_activity(entry: dict) -> None:
            if suppress_activity["value"]:
                return
            state.activity_queue.put(("activity", entry))

        def _run_prepare() -> None:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            box = state.context_box
            workspace_context = box["workspace_context"]
            attachments = box["attachments"]
            previous_messages = box["previous_messages"]
            existing_user_message = None

            from app.domain.services.chat_simple_turn_gate_service import (
                ChatSimpleTurnGateService,
            )

            _on_stream_activity(
                ChatStreamActivityService.entry(
                    verb="Carregando",
                    target="contexto da sessão",
                    phase="prepare",
                    state="active",
                    message=ChatAssistantContentService.get(
                        "stream",
                        "statusPreparingContext",
                    ),
                    entry_id="prepare-session-context",
                )
            )

            suppress_activity["value"] = ChatSimpleTurnGateService.is_simple_turn(
                message=message,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
                attachment_ids=getattr(request, "attachment_ids", None),
            )

            if resend_from_message_id:
                branch_user_message = box.get("user_message")

                if not branch_user_message:
                    raise ChatMessageNotFoundError()

                anchor = self.chat_repository.get_user_message_for_user(
                    message_id=UUID(resend_from_message_id),
                    user_id=user_id,
                    session_id=session_id,
                )

                if not anchor:
                    raise ChatMessageNotFoundError()

                if anchor.session_id != session_id:
                    raise ChatSessionAccessDeniedError()

                all_messages = self.chat_repository.list_all_messages_by_session(session_id)
                existing_user_message = branch_user_message
                history_messages = ChatMessageBranchService.build_path_to_message(
                    all_messages,
                    anchor.parent_message_id,
                )
                previous_messages = all_messages
            else:
                history_messages = None

            should_generate_session_title = self.session_title_service.should_generate(
                session,
                previous_messages,
                resend_from_message_id=resend_from_message_id,
            )

            history_source = history_messages if resend_from_message_id else previous_messages
            agent_meta = workspace_context.get("agent")
            from app.domain.services.chat_advanced_sql_specialist_service import (
                ChatAdvancedSqlSpecialistService,
            )

            agent_max = agent_meta.get("maxToolCalls") if isinstance(agent_meta, dict) else None
            max_tool_calls = ChatAdvancedSqlSpecialistService.resolve_max_tool_calls(
                message,
                agent_max,
            )

            box["history_source"] = history_source
            box["existing_user_message"] = existing_user_message
            box["should_generate_session_title"] = should_generate_session_title
            box["user_message"] = existing_user_message or box.get("user_message")
            box["previous_messages"] = previous_messages

            _on_stream_activity(
                ChatStreamActivityService.entry(
                    verb="Pronto",
                    target="contexto da sessão",
                    phase="prepare",
                    state="done",
                    level="success",
                    message=ChatAssistantContentService.get(
                        "stream",
                        "statusPrepareContextReady",
                    ),
                    entry_id="prepare-session-context",
                )
            )

            state.prepared_box["value"] = self.turn_preparation_service.prepare(
                message=message,
                request=request,
                session=session,
                user_id=user_id,
                workspace_context=workspace_context,
                attachments=attachments,
                previous_messages=previous_messages,
                history_source=history_source,
                build_tool_context=partial(
                    self.turn_support.build_tool_context,
                    agent_context=workspace_context.get("agent"),
                ),
                maybe_extend_tool_context=partial(
                    self.turn_support.maybe_extend_tool_context,
                    request=request,
                ),
                prepare_history=self.turn_support.prepare_history,
                history_keep=Settings.CHAT_HISTORY_MAX_MESSAGES,
                fast_path_enabled=resolve_chat_intelligence_runtime().fast_path_enabled,
                fast_path_max_chars=Settings.CHAT_FAST_PATH_MAX_CHARS,
                resolve_user_identity_answer=lambda msg: (
                    self.turn_support.resolve_user_identity_answer(request.access_token, msg)
                    if request.access_token
                    and ChatUserContextService.is_user_identity_question(msg)
                    else None
                ),
                resolve_capabilities_answer=lambda msg: (
                    self.turn_support.resolve_capabilities_answer(workspace_context, msg)
                    if ChatCapabilitiesService.is_capability_inquiry(msg)
                    else None
                ),
                max_external_action_calls=max_tool_calls,
                on_stream_activity=_on_stream_activity,
                run_post_rag_web_fallback=lambda: self.turn_support.run_post_rag_web_fallback(
                    request,
                    previous_messages=previous_messages,
                    on_stream_activity=_on_stream_activity,
                ),
            )

        def _prepare_worker() -> None:
            try:
                with llm_generation_scope(turn_generation_config):
                    if flask_app is not None:
                        with flask_app.app_context():
                            _run_prepare()
                    else:
                        _run_prepare()
            except Exception as exc:
                state.prepare_error_box["error"] = exc
                try:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    state.activity_queue.put(
                        (
                            "activity",
                            ChatStreamActivityService.entry(
                                verb="Falhou",
                                target="preparação da resposta",
                                phase="prepare",
                                level="error",
                                state="failed",
                                message=ChatAssistantContentService.get(
                                    "stream",
                                    "statusPrepareFailed",
                                ),
                                detail=str(exc)[:300],
                                entry_id="prepare-failed",
                            ),
                        )
                    )
                except Exception:
                    pass
            finally:
                state.activity_queue.put(("done", None))

        threading.Thread(target=_prepare_worker, daemon=True).start()

        return state

    @staticmethod
    def iter_activity_events(state: ChatStreamPrepareWorkerState) -> Iterator[dict]:
        while True:
            kind, payload = state.activity_queue.get()

            if kind == "activity":
                yield {
                    "type": "activity",
                    "entry": payload,
                }
                continue

            if kind == "done":
                break

    @staticmethod
    def raise_if_failed(state: ChatStreamPrepareWorkerState) -> None:
        if state.prepare_error_box.get("error"):
            raise state.prepare_error_box["error"]

    @staticmethod
    def prepared_value(state: ChatStreamPrepareWorkerState):
        return state.prepared_box["value"]
