"""Preferências persistentes de correção textual (memória da sessão + mensagem)."""

from __future__ import annotations

import json
import re
from typing import Any


class ChatTextCorrectionPreferenceService:
    _PERSISTENT_MARKERS = (
        r"\bdaqui\s+pra\s+frente\b",
        r"\bde\s+agora\s+em\s+diante\b",
        r"\bsempre\b",
        r"\bnas\s+pr[oó]ximas\b",
        r"\bnesta\s+conversa\b",
    )

    _CORRECTION_CONTEXT = (
        r"\bcorrij",
        r"\brevise\b",
        r"\btexto\b",
        r"\bortografia\b",
        r"\bgramática\b",
        r"\bgramatica\b",
    )

    _PATTERNS: dict[str, tuple[str, ...]] = {
        "deliverFinalOnly": (
            r"\b(só|somente|apenas)\s+(a\s+)?versão\s+final\b",
            r"\bentregue\s+só\b",
            r"\bsem\s+explica[cç][aã]o\b",
            r"\bapenas\s+a\s+vers[aã]o\s+corrigida\b",
        ),
        "showBeforeAfter": (
            r"\bsempre\b.*\bantes\s+e\s+depois\b",
            r"\bsempre\b.*\bmostre\s+.*\baltera",
            r"\bsempre\b.*\bcompar",
        ),
        "formalTone": (
            r"\bsempre\b.*\bformal\b",
            r"\bsempre\b.*\bcorporativ",
            r"\bcorrij.*\bsempre\b.*\bformal",
        ),
        "preserveStyle": (
            r"\bsempre\b.*\bmant(enha|enha)\b.*\bestilo",
            r"\bsempre\b.*\bsem\s+mudar\b.*\bestilo",
            r"\bsempre\b.*\bmeu\s+estilo",
        ),
        "explainChanges": (
            r"\bsempre\b.*\bexplique\b",
            r"\bsempre\b.*\bo\s+que\s+mudou\b",
            r"\bsempre\b.*\bmostre\s+.*\baltera",
        ),
    }

    _LABELS: dict[str, str] = {
        "deliverFinalOnly": "Só versão final",
        "showBeforeAfter": "Antes e depois",
        "formalTone": "Tom formal",
        "preserveStyle": "Manter estilo",
        "explainChanges": "Explicar alterações",
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
    def _detect_from_message(cls, message: str | None) -> dict[str, bool]:
        prefs: dict[str, bool] = {}
        normalized = (message or "").strip().lower()

        if not normalized:
            return prefs

        persistent = any(re.search(pattern, normalized) for pattern in cls._PERSISTENT_MARKERS)
        correction_context = any(
            re.search(pattern, normalized) for pattern in cls._CORRECTION_CONTEXT
        ) or "correção" in normalized or "correcao" in normalized

        for key, patterns in cls._PATTERNS.items():
            if not any(re.search(pattern, normalized) for pattern in patterns):
                continue

            if persistent or correction_context or key == "deliverFinalOnly":
                prefs[key] = True

        return prefs

    @classmethod
    def _load_from_working_memory(cls, working_memory: dict | None) -> dict[str, bool]:
        prefs: dict[str, bool] = {}

        if not working_memory:
            return prefs

        stored = working_memory.get("textCorrectionPreferences")

        if isinstance(stored, dict):
            prefs.update({key: bool(value) for key, value in stored.items()})

        behavior = working_memory.get("behaviorInstructions") or {}

        if isinstance(behavior, dict):
            prefs.update(cls._parse_text_correction_behavior(behavior.get("textCorrection")))

        if str((behavior or {}).get("finalVersionOnly") or "").lower() in {"true", "1", "yes"}:
            prefs["deliverFinalOnly"] = True

        return prefs

    @classmethod
    def _parse_text_correction_behavior(cls, raw: Any) -> dict[str, bool]:
        if isinstance(raw, dict):
            return {key: bool(value) for key, value in raw.items()}

        if not raw:
            return {}

        text = str(raw).strip()

        if not text:
            return {}

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}

        if isinstance(parsed, dict):
            return {key: bool(value) for key, value in parsed.items()}

        return {}

    @classmethod
    def format_prompt_block(cls, preferences: dict[str, bool] | None) -> str:
        prefs = preferences or {}

        if not prefs:
            return ""

        lines = ["Preferências de correção nesta sessão:"]

        if prefs.get("deliverFinalOnly"):
            lines.append("- Entregue apenas a versão final corrigida, sem explicação longa.")
        if prefs.get("showBeforeAfter"):
            lines.append("- Use seções Antes / Depois / O que mudou quando corrigir.")
        if prefs.get("formalTone"):
            lines.append("- Use tom formal corporativo por padrão nas correções.")
        if prefs.get("preserveStyle"):
            lines.append("- Preserve o estilo original; corrija só ortografia e concordância.")
        if prefs.get("explainChanges"):
            lines.append("- Liste os principais ajustes após a versão corrigida.")

        return "\n".join(lines)

    @classmethod
    def merge_into_behavior(
        cls,
        message: str | None,
        behavior: dict[str, str] | None,
    ) -> dict[str, str]:
        merged = dict(behavior or {})
        existing = cls._parse_text_correction_behavior(merged.get("textCorrection"))
        incoming = cls._detect_from_message(message)
        combined = {**existing, **incoming}

        if not combined:
            return merged

        merged["textCorrection"] = json.dumps(combined, ensure_ascii=False)

        normalized = (message or "").lower()

        if any(re.search(pattern, normalized) for pattern in cls._PERSISTENT_MARKERS):
            merged["scope"] = merged.get("scope") or "session"

        if combined.get("deliverFinalOnly"):
            merged["finalVersionOnly"] = "true"

        return merged

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None = None) -> dict:
        prefs = cls.detect(message, working_memory=snapshot)
        snapshot["textCorrectionPreferences"] = prefs
        return snapshot

    @classmethod
    def build_context_chips(cls, preferences: dict[str, bool] | None) -> list[dict[str, str]]:
        chips: list[dict[str, str]] = []

        for key, enabled in (preferences or {}).items():
            if not enabled:
                continue

            label = cls._LABELS.get(key)

            if not label:
                continue

            chips.append(
                {
                    "label": label,
                    "kind": "textCorrectionPreference",
                    "value": key,
                }
            )

        return chips

    @classmethod
    def build_metadata(cls, preferences: dict[str, bool] | None) -> dict[str, Any] | None:
        prefs = preferences or {}

        if not prefs:
            return None

        active = [cls._LABELS.get(key, key) for key, enabled in prefs.items() if enabled]

        return {
            "active": prefs,
            "labels": active,
            "persisted": True,
        }
