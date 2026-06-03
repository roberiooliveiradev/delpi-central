"""Filtro de segurança de memória — Playbook §23 / Fase 7."""

from __future__ import annotations

import re
from typing import Any


class ChatContextSafetyFilterService:
    _SENSITIVE_RE = re.compile(
        r"\b(?:senha|password|token|api[_-]?key|cpf|cart[aã]o|chave\s+privada|"
        r"secret|bearer\s+)\b",
        re.IGNORECASE,
    )
    _CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    _WRITE_BLOCK_RE = re.compile(
        r"\b(?:n[aã]o\s+salve|n[aã]o\s+grave|sem\s+mem[oó]ria|modo\s+an[oô]nimo)\b",
        re.IGNORECASE,
    )

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None) -> dict:
        result = dict(snapshot)
        normalized = (message or "").strip()
        reasons: list[str] = []

        state = dict(result.get("conversationState") or {})

        if state.get("skipMemoryWrite"):
            reasons.append("sensitive_turn_flag")

        if cls._SENSITIVE_RE.search(normalized) or cls._CPF_RE.search(normalized):
            state["skipMemoryWrite"] = True
            reasons.append("sensitive_content_detected")

        if cls._WRITE_BLOCK_RE.search(normalized):
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

            if cls._SENSITIVE_RE.search(value) or cls._CPF_RE.search(value):
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
