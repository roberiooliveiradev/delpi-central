"""Contexto compacto da sessão para o planner — Topic Ledger, sem dump de histórico."""

from __future__ import annotations

import json
from typing import Any

from app.domain.services.chat_conversation_state_service import ChatConversationStateService


class ChatPlannerConversationContextService:
    _MAX_TOPICS = 8
    _MAX_RECENT = 4
    _FOCUS_ENTITY_KEYS = (
        "productCode",
        "branch",
        "warehouse",
        "period",
        "code",
        "sku",
        "filial",
    )

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
        sticky_active = state.get("stickyContextActive")
        topic_shifted = bool(state.get("preferencesTopicChanged"))
        focus: dict[str, Any] = {}
        if isinstance(workspace_context, dict):
            working = workspace_context.get("workingMemory")
            if isinstance(working, dict):
                raw_focus = working.get("operationalFocus")
                # After topic shift, focus is not argument authority (ledger holds inactive topics).
                if isinstance(raw_focus, dict) and sticky_active is not False and not topic_shifted:
                    focus = cls._normalize_operational_focus(raw_focus)

        last_action = cls._last_action(previous_messages)
        recent = cls._recent_user_messages(previous_messages)
        ctx_params = {}
        if isinstance(execution_context, dict):
            raw = execution_context.get("parameters")
            if isinstance(raw, dict):
                ctx_params = {k: v for k, v in raw.items() if v not in (None, "")}

        # Enrich active topic entities from focus when ledger is still empty.
        if focus.get("entities") and active_id:
            enriched_topics = []
            for topic in topics:
                if not isinstance(topic, dict):
                    continue
                row = dict(topic)
                if str(row.get("topicId") or "") == active_id and not row.get("entities"):
                    row["entities"] = dict(focus["entities"])
                enriched_topics.append(row)
            topics = enriched_topics

        payload = {
            "activeTopicId": active_id or None,
            "topics": topics,
            "operationalFocus": focus,
            "lastSuccessfulAction": last_action,
            "resolvedParameters": ctx_params,
            "recentUserTurns": recent,
            "contextPrecedence": [
                "current_turn_explicit",
                "referenced_topic",
                "active_topic",
                "planner_grounded_proposal",
                "openapi_default",
                "clarify",
            ],
            "rule": (
                "Precedence: (1) explicit values in the current turn win; "
                "(2) explicit reference to a prior topic; (3) resumed topic state; "
                "(4) active topic entities/args; (5) planner grounded proposal; "
                "(6) OpenAPI default; (7) missing required → clarify. "
                "lastSuccessfulAction is evidence only (actionId/path), never argument authority. "
                "Do not reuse product/branch/timeRange from a non-referenced inactive topic."
            ),
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    @classmethod
    def _normalize_operational_focus(cls, raw_focus: dict[str, Any]) -> dict[str, Any]:
        """WM stores flat productCode/branch/period; planner expects entities/timeRange/label."""
        nested_entities = raw_focus.get("entities")
        entities: dict[str, Any] = {}
        if isinstance(nested_entities, dict) and nested_entities:
            entities = {
                key: value
                for key, value in nested_entities.items()
                if value not in (None, "", {}, [])
            }
        else:
            for key in cls._FOCUS_ENTITY_KEYS:
                value = raw_focus.get(key)
                if value not in (None, "", {}, []):
                    entities[key] = value

        time_range = raw_focus.get("timeRange")
        if not isinstance(time_range, dict):
            time_range = {}
            period = raw_focus.get("period")
            if isinstance(period, dict):
                time_range = {
                    key: value
                    for key, value in period.items()
                    if value not in (None, "")
                }
            elif period not in (None, ""):
                time_range = {"label": period}

        label = str(raw_focus.get("label") or "").strip()
        if not label and entities.get("productCode"):
            label = str(entities.get("productCode"))

        focus: dict[str, Any] = {}
        if entities:
            focus["entities"] = entities
        if time_range:
            focus["timeRange"] = time_range
        if label:
            focus["label"] = label
        return focus

    @classmethod
    def _message_role(cls, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("role") or "").strip().lower()
        return str(getattr(item, "role", "") or "").strip().lower()

    @classmethod
    def _message_metadata(cls, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            meta = item.get("metadata")
            return meta if isinstance(meta, dict) else {}
        meta = getattr(item, "metadata", None)
        return meta if isinstance(meta, dict) else {}

    @classmethod
    def _message_content(cls, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("content") or item.get("message") or "").strip()
        return str(getattr(item, "content", "") or "").strip()

    @classmethod
    def _last_action(cls, previous_messages: list | None) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "assistant":
                continue
            metadata = cls._message_metadata(item)
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
                action_id = str(arguments.get("actionId") or meta.get("actionId") or "").strip()
                path = str(meta.get("path") or "").strip()
                if not action_id and not path:
                    continue
                return {
                    "role": "evidence",
                    "actionId": action_id,
                    "path": path,
                }
        return None

    @classmethod
    def _recent_user_messages(cls, previous_messages: list | None) -> list[str]:
        rows: list[str] = []
        for item in previous_messages or []:
            if cls._message_role(item) != "user":
                continue
            text = cls._message_content(item)
            if text:
                rows.append(text[:240])
        return rows[-cls._MAX_RECENT :]
