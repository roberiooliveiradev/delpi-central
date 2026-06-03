"""Orquestração do contexto avançado — Playbook memória Fase 7."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_context_safety_filter_service import (
    ChatContextSafetyFilterService,
)
from app.domain.services.chat_learned_forgetting_service import ChatLearnedForgettingService
from app.domain.services.chat_memory_contradiction_service import (
    ChatMemoryContradictionService,
)
from app.domain.services.chat_memory_context_debug_service import (
    ChatMemoryContextDebugService,
)
from app.domain.services.chat_memory_knowledge_graph_service import (
    ChatMemoryKnowledgeGraphService,
)


class ChatAdvancedContextService:
    @classmethod
    def apply_pre_turn(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        previous_messages: list[Any] | None = None,
    ) -> dict:
        result = dict(snapshot)
        result = ChatMemoryContradictionService.apply_to_snapshot(result, message=message)
        result = ChatLearnedForgettingService.apply_to_snapshot(result, message=message)
        result = ChatMemoryKnowledgeGraphService.apply_to_snapshot(result)
        result = ChatContextSafetyFilterService.apply_to_snapshot(result, message=message)
        result = ChatMemoryContextDebugService.apply_to_snapshot(result)
        return result

    @classmethod
    def apply_post_turn(
        cls,
        snapshot: dict,
        *,
        message: str | None = None,
    ) -> dict:
        result = dict(snapshot)

        if not ChatContextSafetyFilterService.should_allow_persist(result):
            result["memoryWriteGated"] = True
            return ChatMemoryContextDebugService.apply_to_snapshot(result)

        result = ChatMemoryContradictionService.apply_to_snapshot(result, message=message)
        result = ChatMemoryKnowledgeGraphService.apply_to_snapshot(result)
        return ChatMemoryContextDebugService.apply_to_snapshot(result)

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        blocks = [
            ChatMemoryContradictionService.format_prompt_block(snapshot),
            ChatMemoryKnowledgeGraphService.format_prompt_block(snapshot),
        ]
        merged = "\n".join(block for block in blocks if block)

        return merged or None

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        return ChatMemoryContextDebugService.compact_for_admin_debug(snapshot)
