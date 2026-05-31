"""Preferências de sessão para tarefas textuais — Playbook 03 §22."""

from __future__ import annotations

import re
from typing import Any


class ChatTextTaskPreferenceService:
    _PREFERENCE_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"sempre\s+corrij[ao]?\s+sem\s+explicar", "deliver_final_only"),
        (r"so\s+vers[aã]o\s+final", "deliver_final_only"),
        (r"sempre\s+mostre\s+antes\s+e\s+depois", "show_diff"),
        (r"sempre\s+deixe\s+mais\s+formal", "tone_formal"),
        (r"sempre\s+use\s+linguagem\s+simples", "tone_simple"),
        (r"sempre\s+ger[eo]\s+assunto", "email_subject"),
        (r"sempre\s+em\s+t[oó]picos", "format_topics"),
        (r"sempre\s+resumo\s+executivo", "summary_executive"),
    )

    @classmethod
    def detect_from_message(cls, message: str | None) -> dict[str, Any]:
        normalized = (message or "").strip().lower()
        prefs: dict[str, Any] = {}

        for pattern, key in cls._PREFERENCE_PATTERNS:
            if re.search(pattern, normalized):
                prefs[key] = True

        return prefs

    @classmethod
    def merge_into_behavior(cls, message: str | None, behavior: dict | None) -> dict:
        behavior = dict(behavior or {})
        prefs = cls.detect_from_message(message)

        if prefs:
            text_prefs = dict(behavior.get("textTask") or {})
            text_prefs.update(prefs)
            behavior["textTask"] = text_prefs

        return behavior

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None = None) -> None:
        prefs = cls.detect_from_message(message)
        working = snapshot.setdefault("preferences", {})

        if prefs:
            working["textTask"] = prefs

    @classmethod
    def format_prompt_block(cls, workspace_context: dict | None) -> str | None:
        working = (workspace_context or {}).get("workingMemory") or {}
        prefs = (working.get("preferences") or {}).get("textTask")

        if not isinstance(prefs, dict) or not prefs:
            return None

        lines = ["Preferências textuais da sessão:"]

        labels = {
            "deliver_final_only": "entregar só versão final",
            "show_diff": "mostrar antes e depois",
            "tone_formal": "tom formal",
            "tone_simple": "linguagem simples",
            "email_subject": "sempre sugerir assunto",
            "format_topics": "formato em tópicos",
            "summary_executive": "resumo executivo",
        }

        for key, label in labels.items():
            if prefs.get(key):
                lines.append(f"- {label}")

        return "\n".join(lines) if len(lines) > 1 else None

    @classmethod
    def build_ack_direct_answer(cls, message: str | None) -> str | None:
        prefs = cls.detect_from_message(message)

        if not prefs:
            return None

        return "Combinado. Nesta conversa, vou seguir essa preferência textual."
