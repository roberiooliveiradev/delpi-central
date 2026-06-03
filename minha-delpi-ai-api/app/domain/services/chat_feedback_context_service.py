"""Contexto técnico de feedback — Playbook 10 (métricas e feedback)."""

from __future__ import annotations

import re
from typing import Any


class ChatFeedbackContextService:
    _SENSITIVE_COMMENT_RE = re.compile(
        r"\b\d{6,}\b|@[\w.-]+\.\w+|sk-[a-zA-Z0-9]{8,}",
        re.IGNORECASE,
    )

    @classmethod
    def snapshot_from_assistant_metadata(
        cls,
        metadata: dict[str, Any] | None,
        *,
        session_id: str | None = None,
        agent_id: str | None = None,
        agent_name: str | None = None,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        metadata = metadata if isinstance(metadata, dict) else {}
        intent_routing = metadata.get("intentRouting")

        if not isinstance(intent_routing, dict):
            intent_routing = {}

        router_metrics = metadata.get("intentRouterMetrics")

        if not isinstance(router_metrics, dict):
            router_metrics = {}

        tool_calls = metadata.get("toolCalls") if isinstance(metadata.get("toolCalls"), list) else []
        tool_path = cls._primary_tool_path(tool_calls)
        rag = metadata.get("rag") if isinstance(metadata.get("rag"), dict) else {}
        web_research = metadata.get("webSearchResearch")
        web_metrics = metadata.get("webSearchMetrics")
        admin_debug = metadata.get("adminDebug") if isinstance(metadata.get("adminDebug"), dict) else {}
        interactivity = metadata.get("interactivity") if isinstance(metadata.get("interactivity"), dict) else {}
        error_handling = metadata.get("errorHandling") if isinstance(metadata.get("errorHandling"), dict) else {}
        presentation = metadata.get("presentationMetrics")

        if not isinstance(presentation, dict):
            presentation = metadata.get("presentation") if isinstance(metadata.get("presentation"), dict) else {}

        memory_used = cls._memory_used(metadata, admin_debug)
        assertiveness = metadata.get("contextAssertiveness")
        memory_assertiveness_score = None

        if isinstance(assertiveness, dict) and assertiveness.get("score") is not None:
            memory_assertiveness_score = assertiveness.get("score")
        suggestions = interactivity.get("suggestionsShown") or interactivity.get("suggestions") or []

        shown_labels: list[str] = []

        if isinstance(suggestions, list):
            for item in suggestions:
                if isinstance(item, str) and item.strip():
                    shown_labels.append(item.strip())
                elif isinstance(item, dict):
                    label = str(item.get("label") or "").strip()

                    if label:
                        shown_labels.append(label)

        error_value = error_handling.get("error") or error_handling.get("code")
        sql_advanced = metadata.get("sqlAdvanced") if isinstance(metadata.get("sqlAdvanced"), dict) else {}
        sql_metrics = (
            metadata.get("sqlAdvancedMetrics")
            if isinstance(metadata.get("sqlAdvancedMetrics"), dict)
            else {}
        )
        text_task = metadata.get("textTask") if isinstance(metadata.get("textTask"), dict) else {}
        text_assistant = (
            metadata.get("textAssistant")
            if isinstance(metadata.get("textAssistant"), dict)
            else {}
        )
        text_metrics = (
            metadata.get("textTaskMetrics")
            if isinstance(metadata.get("textTaskMetrics"), dict)
            else {}
        )

        return {
            "sessionId": session_id,
            "intent": intent_routing.get("intent") or router_metrics.get("intent"),
            "subIntent": intent_routing.get("subIntent") or router_metrics.get("subIntent"),
            "confidence": intent_routing.get("confidence") or router_metrics.get("confidence"),
            "agentId": agent_id,
            "agent": agent_name,
            "usedTool": bool(tool_calls),
            "toolPath": tool_path,
            "usedRag": cls._rag_used(rag),
            "usedWeb": bool(web_research or web_metrics),
            "usedMemory": memory_used,
            "memoryAssertivenessScore": memory_assertiveness_score,
            "presentationType": cls._presentation_type(presentation, tool_calls),
            "durationMs": duration_ms or cls._duration_ms(admin_debug, metadata),
            "error": str(error_value).strip() if error_value else None,
            "suggestionsShown": shown_labels[:12],
            "sqlMode": sql_metrics.get("mode") or sql_advanced.get("mode"),
            "sqlDialect": sql_metrics.get("dialect")
            or (sql_advanced.get("dialect") or {}).get("dialect")
            if isinstance(sql_advanced.get("dialect"), dict)
            else None,
            "sqlBlocked": sql_metrics.get("blocked") if "blocked" in sql_metrics else sql_advanced.get("blocked"),
            "sqlEmptyResult": sql_metrics.get("emptyResult"),
            "textTaskSubtype": (
                text_task.get("subtype")
                or text_assistant.get("subtype")
                or text_metrics.get("subtype")
            ),
            "textTaskIntent": (
                text_task.get("intent")
                or text_assistant.get("intent")
                or text_metrics.get("intent")
            ),
            "textTaskType": (
                text_task.get("type")
                or text_assistant.get("type")
                or text_metrics.get("type")
            ),
        }

    @classmethod
    def sanitize_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        if not normalized:
            return None

        masked = cls._SENSITIVE_COMMENT_RE.sub("[redacted]", normalized)

        return masked[:500]

    @classmethod
    def _primary_tool_path(cls, tool_calls: list[Any]) -> str | None:
        for call in tool_calls:
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
            path = str(metadata.get("path") or call.get("path") or "").strip()

            if path:
                return path[:240]

            action_id = str((call.get("arguments") or {}).get("actionId") or "").strip()

            if action_id:
                return action_id[:240]

        return None

    @classmethod
    def _rag_used(cls, rag: dict[str, Any]) -> bool:
        sources = rag.get("sources")

        if isinstance(sources, list) and sources:
            return True

        return bool(rag.get("enabled") or rag.get("chunkCount") or rag.get("documentCount"))

    @classmethod
    def _memory_used(cls, metadata: dict[str, Any], admin_debug: dict[str, Any]) -> bool:
        if metadata.get("contextSnapshot"):
            return True

        memory = admin_debug.get("memory")

        if isinstance(memory, dict) and memory.get("used"):
            return True

        session_memory = admin_debug.get("sessionMemoryMetrics")

        if isinstance(session_memory, dict) and session_memory.get("entriesUsed"):
            return True

        return False

    @classmethod
    def _presentation_type(cls, presentation: dict[str, Any], tool_calls: list[Any]) -> str | None:
        selected = presentation.get("presentationType") or presentation.get("selected")

        if selected:
            return str(selected)

        for call in tool_calls:
            if not isinstance(call, dict):
                continue

            presentation_type = (call.get("metadata") or {}).get("presentationType")

            if presentation_type:
                return str(presentation_type)

        return None

    @classmethod
    def _duration_ms(cls, admin_debug: dict[str, Any], metadata: dict[str, Any]) -> int | None:
        intelligence = admin_debug.get("intelligence")

        if isinstance(intelligence, dict):
            timings = intelligence.get("timings")

            if isinstance(timings, dict):
                total = timings.get("totalMs") or timings.get("latencyMs")

                if total is not None:
                    try:
                        return int(total)
                    except (TypeError, ValueError):
                        pass

        response_metadata = metadata.get("responseMetadata")

        if isinstance(response_metadata, dict) and response_metadata.get("durationMs") is not None:
            try:
                return int(response_metadata["durationMs"])
            except (TypeError, ValueError):
                pass

        return None
