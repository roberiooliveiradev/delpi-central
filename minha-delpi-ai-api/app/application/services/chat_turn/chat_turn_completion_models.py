"""Modelos compartilhados — conclusão de turno (send/stream)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_pipeline_timings import ChatPipelineTimings

if TYPE_CHECKING:
    from app.application.services.chat_turn.chat_turn_preparation_service import (
        ChatTurnPreparationResult,
    )


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
class ChatTurnCompletionFinalizeResult:
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
