"""Preferências de sessão para tarefas textuais — Playbook editor textual §20."""

from __future__ import annotations

import json
import re
from typing import Any


class ChatTextTaskPreferenceService:
    _PERSISTENT_MARKERS = (
        r"\bdaqui\s+pra\s+frente\b",
        r"\bde\s+agora\s+em\s+diante\b",
        r"\bsempre\b",
        r"\bnas\s+pr[oó]ximas\b",
        r"\bnesta\s+conversa\b",
    )

    _TEXT_CONTEXT = (
        r"\btexto\b",
        r"\be-?mail\b",
        r"\bcarta\b",
        r"\bata\b",
        r"\bcomunicado\b",
        r"\bresumo\b",
        r"\bcorrij",
        r"\breescrev",
        r"\btraduz",
    )

    _PATTERNS: dict[str, tuple[str, ...]] = {
        "deliver_final_only": (
            r"\bsempre\s+corrij[ao]?\s+sem\s+explicar\b",
            r"\bso\s+vers[aã]o\s+final\b",
            r"\bs[oó]\s+corrij[ao]?\s+sem\s+explicar\b",
            r"\bde\s+agora\s+em\s+diante\b.*\bsem\s+explicar\b",
            r"\bde\s+agora\s+em\s+diante\b.*\bvers[aã]o\s+final\b",
            r"\bapenas\s+a\s+vers[aã]o\s+corrigida\b",
        ),
        "show_diff": (
            r"\bsempre\s+mostre\s+antes\s+e\s+depois\b",
            r"\bsempre\b.*\bantes\s+e\s+depois\b",
        ),
        "tone_formal": (
            r"\bsempre\s+deixe\s+mais\s+formal\b",
            r"\bsempre\s+em\s+portugu[eê]s\s+formal\b",
        ),
        "tone_simple": (r"\bsempre\s+use\s+linguagem\s+simples\b",),
        "email_subject": (
            r"\bsempre\s+ger[eo]\s+assunto\b",
            r"\bsempre\s+com\s+assunto\b",
        ),
        "email_direct": (
            r"\bsempre\s+deixe\s+meus\s+e-?mails\s+mais\s+diretos\b",
            r"\bsempre\s+e-?mails\s+mais\s+diretos\b",
            r"\bsempre\s+deixe\s+os\s+e-?mails\s+mais\s+objetivos\b",
        ),
        "format_topics": (
            r"\bsempre\s+(?:me\s+entregue\s+)?em\s+t[oó]picos\b",
            r"\bde\s+agora\s+em\s+diante\b.*\bem\s+t[oó]picos\b",
        ),
        "summary_executive": (r"\bsempre\s+resumo\s+executivo\b",),
        "three_versions": (r"\bsempre\s+tr[eê]s\s+vers[oõ]es\b",),
        "preserve_style": (
            r"\bsempre\b.*\bpreserv\w*\s+meu\s+estilo\b",
            r"\bsempre\b.*\bsem\s+mudar\b.*\bestilo\b",
            r"\bcorrija\s+sem\s+mudar\s+meu\s+estilo\b",
        ),
        "suggest_improvements": (r"\bsempre\s+sugira\s+melhorias\b",),
        "explain_changes": (
            r"\bsempre\s+explique\s+altera",
            r"\bsempre\s+explique\s+o\s+que\s+mudou\b",
        ),
    }

    _LABELS: dict[str, str] = {
        "deliver_final_only": "Só versão final",
        "show_diff": "Antes e depois",
        "tone_formal": "Tom formal",
        "tone_simple": "Linguagem simples",
        "email_subject": "Sempre com assunto",
        "email_direct": "E-mails diretos",
        "format_topics": "Formato em tópicos",
        "summary_executive": "Resumo executivo",
        "three_versions": "Três versões",
        "preserve_style": "Preservar estilo",
        "suggest_improvements": "Sugerir melhorias",
        "explain_changes": "Explicar alterações",
    }

    @classmethod
    def detect(
        cls,
        message: str | None,
        *,
        working_memory: dict | None = None,
    ) -> dict[str, bool]:
        prefs: dict[str, bool] = {}
        prefs.update(cls._load_from_working_memory(working_memory))
        prefs.update(cls._detect_from_message(message))
        return {key: value for key, value in prefs.items() if value}

    @classmethod
    def detect_from_message(cls, message: str | None) -> dict[str, Any]:
        return cls._detect_from_message(message)

    @classmethod
    def _detect_from_message(cls, message: str | None) -> dict[str, bool]:
        prefs: dict[str, bool] = {}
        normalized = (message or "").strip().lower()

        if not normalized:
            return prefs

        persistent = any(re.search(pattern, normalized) for pattern in cls._PERSISTENT_MARKERS)
        text_context = any(re.search(pattern, normalized) for pattern in cls._TEXT_CONTEXT)

        for key, patterns in cls._PATTERNS.items():
            if not any(re.search(pattern, normalized) for pattern in patterns):
                continue

            if persistent or text_context or key in {"deliver_final_only", "preserve_style"}:
                prefs[key] = True

        return prefs

    @classmethod
    def _load_from_working_memory(cls, working_memory: dict | None) -> dict[str, bool]:
        if not isinstance(working_memory, dict):
            return {}

        nested = (working_memory.get("preferences") or {}).get("textTask")

        if isinstance(nested, dict):
            return {key: bool(value) for key, value in nested.items() if value}

        behavior = working_memory.get("behaviorInstructions") or {}
        raw = behavior.get("textTaskWriting")

        if not raw:
            return {}

        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return {}

        if isinstance(parsed, dict):
            return {key: bool(value) for key, value in parsed.items() if value}

        return {}

    @classmethod
    def merge_into_behavior(cls, message: str | None, behavior: dict | None) -> dict:
        merged = dict(behavior or {})
        existing = cls._parse_behavior(merged.get("textTaskWriting"))
        incoming = cls._detect_from_message(message)
        combined = {**existing, **incoming}

        if not combined:
            return merged

        merged["textTaskWriting"] = json.dumps(combined, ensure_ascii=False)
        normalized = (message or "").lower()

        if any(re.search(pattern, normalized) for pattern in cls._PERSISTENT_MARKERS):
            merged["scope"] = merged.get("scope") or "session"

        if combined.get("deliver_final_only"):
            merged["finalVersionOnly"] = "true"

        if combined.get("tone_formal"):
            merged["tone"] = "formal"

        if combined.get("email_direct"):
            merged["tone"] = merged.get("tone") or "direct"

        return merged

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None = None) -> None:
        prefs = cls.detect(message, working_memory=snapshot)
        working = snapshot.setdefault("preferences", {})
        existing = dict(working.get("textTask") or {})
        working["textTask"] = {**existing, **prefs}
        snapshot["textTaskPreferences"] = working["textTask"]

    @classmethod
    def get_active_prefs(cls, workspace_context: dict | None) -> dict[str, bool]:
        working = (workspace_context or {}).get("workingMemory") or {}
        return cls.detect(None, working_memory=working)

    @classmethod
    def format_prompt_block(cls, workspace_context: dict | None) -> str | None:
        prefs = cls.get_active_prefs(workspace_context)

        if not prefs:
            return None

        lines = ["Preferências textuais da sessão:"]

        for key, label in cls._LABELS.items():
            if prefs.get(key):
                lines.append(f"- {label}")

        return "\n".join(lines) if len(lines) > 1 else None

    @classmethod
    def build_ack_direct_answer(cls, message: str | None) -> str | None:
        prefs = cls._detect_from_message(message)

        if not prefs:
            return None

        return "Combinado. Nesta conversa, vou seguir essa preferência textual."

    @staticmethod
    def _parse_behavior(raw: Any) -> dict[str, bool]:
        if not raw:
            return {}

        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return {}

        if isinstance(parsed, dict):
            return {key: bool(value) for key, value in parsed.items() if value}

        return {}
