"""Debug estruturado de memória/contexto — Playbook Fase 7."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_context_safety_filter_service import (
    ChatContextSafetyFilterService,
)
from app.domain.services.chat_episodic_memory_service import ChatEpisodicMemoryService
from app.domain.services.chat_learned_forgetting_service import ChatLearnedForgettingService
from app.domain.services.chat_memory_contradiction_service import (
    ChatMemoryContradictionService,
)
from app.domain.services.chat_memory_knowledge_graph_service import (
    ChatMemoryKnowledgeGraphService,
)
from app.domain.services.chat_semantic_memory_retriever_service import (
    ChatSemanticMemoryRetrieverService,
)


class ChatMemoryContextDebugService:
    @classmethod
    def apply_to_snapshot(cls, snapshot: dict) -> dict:
        result = dict(snapshot)
        result["memoryContextDebug"] = cls.build(result)
        return result

    @classmethod
    def build(cls, snapshot: dict) -> dict[str, Any]:
        layers: list[str] = []

        if snapshot.get("operationalFocus") or snapshot.get("operationalFocus"):
            layers.append("operationalFocus")

        if snapshot.get("behaviorInstructions") or snapshot.get("userPreferences"):
            layers.append("preferences")

        if snapshot.get("conversationState"):
            layers.append("conversation_state")

        if snapshot.get("compressedContext") or snapshot.get("conversationSummary"):
            layers.append("compression")

        if snapshot.get("semanticMemoryRequested"):
            layers.append("semantic")

        if snapshot.get("episodicMemory") or snapshot.get("episodicRecall"):
            layers.append("episodic")

        if snapshot.get("memoryGraph"):
            layers.append("knowledge_graph")

        return {
            "layers": layers,
            "usedMemoryKeys": snapshot.get("usedMemoryKeys") or [],
            "memoryUsed": bool(snapshot.get("memoryUsed")),
            "contradiction": ChatMemoryContradictionService.compact_for_admin_debug(snapshot),
            "safety": ChatContextSafetyFilterService.compact_for_admin_debug(snapshot),
            "forgetting": ChatLearnedForgettingService.compact_for_admin_debug(snapshot),
            "semantic": ChatSemanticMemoryRetrieverService.compact_for_admin_debug(snapshot),
            "episodic": ChatEpisodicMemoryService.compact_for_admin_debug(snapshot),
            "graph": ChatMemoryKnowledgeGraphService.compact_for_admin_debug(snapshot),
            "writeAllowed": ChatContextSafetyFilterService.should_allow_persist(snapshot),
        }

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        debug = (snapshot or {}).get("memoryContextDebug")

        if isinstance(debug, dict):
            return debug

        return cls.build(snapshot or {})
