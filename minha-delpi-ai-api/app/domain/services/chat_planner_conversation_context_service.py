"""Contexto compacto da sessão para o planner — Topic Ledger, sem dump de histórico."""

from __future__ import annotations

import json
from typing import Any

from app.domain.services.chat_conversation_state_service import ChatConversationStateService


class ChatPlannerConversationContextService:
    _MAX_TOPICS = 8
    _MAX_RECENT = 4

    @classmethod
    def build(
        cls,
        *,
        previous_messages: list | None,
        workspace_context: dict[str, Any] | None,
        execution_context: dict[str, Any] | None,
    ) -> str:
        snapshot = {}
        if isinstance(workspace_context, dict):
            working = workspace_context.get("workingMemory")
            if isinstance(working, dict):
                snapshot = dict(working)
            state = workspace_context.get("conversationState") or (
                working.get("conversationState") if isinstance(working, dict) else None
            )
            if isinstance(state, dict):
                snapshot["conversationState"] = state

        state = ChatConversationStateService.ensure_topic_ledger(
            snapshot.get("conversationState")
            if isinstance(snapshot.get("conversationState"), dict)
            else ChatConversationStateService.load_from_previous_messages(previous_messages)
        )
        topics = list(state.get("topics") or [])[-cls._MAX_TOPICS :]
        active_id = str(state.get("activeTopicId") or state.get("activeTopic") or "").strip()
        focus = {}
        if isinstance(workspace_context, dict):
            working = workspace_context.get("workingMemory")
            if isinstance(working, dict):
                raw_focus = working.get("operationalFocus")
                if isinstance(raw_focus, dict):
                    focus = dict(raw_focus)

        last_action = cls._last_action(previous_messages)
        recent = cls._recent_user_messages(previous_messages)
        ctx_params = {}
        if isinstance(execution_context, dict):
            raw = execution_context.get("parameters")
            if isinstance(raw, dict):
                ctx_params = {k: v for k, v in raw.items() if v not in (None, "")}

        payload = {
            "activeTopicId": active_id or None,
            "topics": topics,
            "operationalFocus": focus,
            "lastSuccessfulAction": last_action,
            "resolvedParameters": ctx_params,
            "recentUserTurns": recent,
            "rule": (
                "Current-turn explicit values win. Do not reuse product/branch/timeRange "
                "from a non-referenced topic after a topic shift. Resume only via topicId listed above."
            ),
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    @classmethod
    def _last_action(cls, previous_messages: list | None) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            if not isinstance(item, dict):
                continue
            if str(item.get("role") or "").strip().lower() != "assistant":
                continue
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            for call in metadata.get("toolCalls") or []:
                if not isinstance(call, dict):
                    continue
                name = str(call.get("name") or "")
                if name != "execute_external_action":
                    continue
                arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
                meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
                if meta.get("ok") is False:
                    continue
                return {
                    "actionId": str(arguments.get("actionId") or meta.get("actionId") or ""),
                    "path": str(meta.get("path") or ""),
                    "parameters": arguments.get("parameters")
                    if isinstance(arguments.get("parameters"), dict)
                    else {},
                }
        return None

    @classmethod
    def _recent_user_messages(cls, previous_messages: list | None) -> list[str]:
        rows: list[str] = []
        for item in previous_messages or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("role") or "").strip().lower() != "user":
                continue
            text = str(item.get("content") or item.get("message") or "").strip()
            if text:
                rows.append(text[:240])
        return rows[-cls._MAX_RECENT :]
