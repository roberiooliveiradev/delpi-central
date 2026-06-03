"""Anexa memória contextual e score de assertividade ao metadata do assistente."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_context_assertiveness_service import (
    ChatContextAssertivenessService,
)
from app.application.services.chat_session_memory_metrics_service import (
    ChatSessionMemoryMetricsService,
)
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_memory_ux_service import ChatMemoryUxService


class ChatContextMetadataService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        answer: str,
        tool_calls: list | None,
        previous_messages: list[Any] | None,
        workspace_context: dict | None,
        session_memory_service=None,
    ) -> None:
        pre_snapshot = (workspace_context or {}).get("workingMemory")

        workspace = workspace_context or {}
        snapshot = ChatConversationMemoryService.build_post_turn(
            message=message,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
            pre_snapshot=pre_snapshot if isinstance(pre_snapshot, dict) else None,
            agent_id=str(workspace.get("agentId") or "") or None,
            project_id=str((workspace.get("project") or {}).get("id") or "") or None,
            answer=answer,
        )

        assertiveness = ChatContextAssertivenessService.evaluate_turn(
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            snapshot=snapshot,
        )

        metadata["contextSnapshot"] = snapshot
        metadata["contextAssertiveness"] = assertiveness
        context_chips = ChatConversationMemoryService.build_context_chips(snapshot)

        if context_chips:
            metadata["contextChips"] = context_chips

        metadata["memoryUx"] = ChatMemoryUxService.build_for_metadata(snapshot)

        ChatSessionMemoryMetricsService.attach_to_assistant_metadata(
            metadata,
            snapshot=snapshot,
        )

        admin_debug = metadata.get("adminDebug")

        if isinstance(admin_debug, dict):
            memory_debug = ChatConversationMemoryService.compact_for_admin_debug(snapshot)

            if session_memory_service:
                memory_debug.update(
                    session_memory_service.compact_for_admin_debug(snapshot)
                )

            memory_debug["resolvedReferences"] = snapshot.get("resolvedReferences") or []
            memory_debug["preferencesApplied"] = snapshot.get("preferencesApplied") or []

            admin_debug["memory"] = memory_debug
            admin_debug["contextAssertiveness"] = assertiveness
            metrics = metadata.get("sessionMemoryMetrics")
            if isinstance(metrics, dict):
                admin_debug["sessionMemoryMetrics"] = metrics
