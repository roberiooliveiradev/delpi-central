"""Anexa memória contextual e score de assertividade ao metadata do assistente."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_context_assertiveness_service import (
    ChatContextAssertivenessService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


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
    ) -> None:
        pre_snapshot = (workspace_context or {}).get("workingMemory")

        snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
            message=message,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
            pre_snapshot=pre_snapshot if isinstance(pre_snapshot, dict) else None,
        )

        assertiveness = ChatContextAssertivenessService.evaluate_turn(
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            snapshot=snapshot,
        )

        metadata["contextSnapshot"] = snapshot
        metadata["contextAssertiveness"] = assertiveness

        admin_debug = metadata.get("adminDebug")

        if isinstance(admin_debug, dict):
            admin_debug["memory"] = ChatWorkingMemoryService.compact_for_admin_debug(snapshot)
            admin_debug["contextAssertiveness"] = assertiveness
