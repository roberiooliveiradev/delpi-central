"""Filtro de segurança de memória — Playbook §23 / Fase 7."""

from __future__ import annotations

from typing import Any


from app.domain.services.chat_memory_intent_content_service import (
    ChatMemoryIntentContentService,
)


class ChatContextSafetyFilterService:
    @classmethod
    def _sensitive_re(cls):
        return ChatMemoryIntentContentService.compile_pattern(
            "contextSafety", "patterns", "sensitive"
        )

    @classmethod
    def _cpf_re(cls):
        return ChatMemoryIntentContentService.compile_pattern(
            "contextSafety", "patterns", "cpf"
        )

    @classmethod
    def _write_block_re(cls):
        return ChatMemoryIntentContentService.compile_pattern(
            "contextSafety", "patterns", "writeBlock"
        )

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None) -> dict:
        result = dict(snapshot)
        normalized = (message or "").strip()
        reasons: list[str] = []

        state = dict(result.get("conversationState") or {})

        if state.get("skipMemoryWrite"):
            reasons.append("sensitive_turn_flag")

        if cls._sensitive_re().search(normalized) or cls._cpf_re().search(normalized):
            state["skipMemoryWrite"] = True
            reasons.append("sensitive_content_detected")

        if cls._write_block_re().search(normalized):
            state["skipMemoryWrite"] = True
            reasons.append("user_requested_no_write")

        result["conversationState"] = state

        if reasons:
            result["memoryWriteGated"] = True
            result["memoryWriteGateReasons"] = list(
                dict.fromkeys((result.get("memoryWriteGateReasons") or []) + reasons)
            )[-6:]

        behavior = dict(result.get("behaviorInstructions") or {})

        for key in list(behavior.keys()):
            value = str(behavior.get(key) or "")

            if cls._sensitive_re().search(value) or cls._cpf_re().search(value):
                behavior.pop(key, None)
                reasons.append(f"stripped_behavior:{key}")

        result["behaviorInstructions"] = behavior
        result["memorySafetyFiltered"] = bool(reasons)

        return result

    @classmethod
    def should_allow_persist(cls, snapshot: dict | None) -> bool:
        snap = snapshot or {}

        if snap.get("memoryWriteGated"):
            return False

        state = snap.get("conversationState") or {}

        if isinstance(state, dict) and state.get("skipMemoryWrite"):
            return False

        return not snap.get("persistedMemoryCleared")

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        return {
            "filtered": bool((snapshot or {}).get("memorySafetyFiltered")),
            "writeGated": bool((snapshot or {}).get("memoryWriteGated")),
            "reasons": (snapshot or {}).get("memoryWriteGateReasons") or [],
        }
