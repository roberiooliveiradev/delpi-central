"""Detecção de intenção para memória semântica — Playbook memória e contexto (Fase 5)."""

from __future__ import annotations

import re

from app.domain.services.chat_memory_intent_content_service import (
    ChatMemoryIntentContentService,
)


class ChatSemanticMemoryIntentService:
    @classmethod
    def _doc_question_re(cls) -> re.Pattern[str]:
        return ChatMemoryIntentContentService.compile_pattern(
            "semantic", "patterns", "docQuestion"
        )

    @classmethod
    def _playbook_re(cls) -> re.Pattern[str]:
        return ChatMemoryIntentContentService.compile_pattern(
            "semantic", "patterns", "playbook"
        )

    @classmethod
    def _operational_block_re(cls) -> re.Pattern[str]:
        return ChatMemoryIntentContentService.compile_pattern(
            "semantic", "patterns", "operationalBlock"
        )

    @classmethod
    def should_enrich_semantic_retrieval(
        cls,
        message: str | None,
        *,
        snapshot: dict | None = None,
    ) -> bool:
        normalized = (message or "").strip()
        min_chars = ChatMemoryIntentContentService.limit_int(
            "semantic",
            "limits",
            "minMessageChars",
            default=8,
        )

        if len(normalized) < min_chars:
            return False

        if cls._operational_block_re().search(normalized) and not cls._doc_question_re().search(
            normalized
        ):
            return False

        if cls._doc_question_re().search(normalized) or cls._playbook_re().search(normalized):
            return True

        snap = snapshot or {}
        state = snap.get("conversationState") or {}
        task = state.get("activeTask")

        if isinstance(task, dict):
            task_type = str(task.get("type") or "")

            if task_type in ChatMemoryIntentContentService.string_list(
                "semantic",
                "enrichTaskTypes",
            ):
                return True

        return bool(snap.get("proceduralMemoryHints"))

    @classmethod
    def intent_kind(cls, message: str | None, *, snapshot: dict | None = None) -> str | None:
        normalized = (message or "").strip()

        if cls._playbook_re().search(normalized):
            return "playbook"

        if cls._doc_question_re().search(normalized):
            return "documentation"

        snap = snapshot or {}
        task = (snap.get("conversationState") or {}).get("activeTask")

        if isinstance(task, dict):
            mapping = ChatMemoryIntentContentService.string_map(
                "semantic",
                "taskTypeIntentMap",
            )

            return mapping.get(str(task.get("type") or "")) or None

        return None
