"""Preferências persistentes de escrita de e-mail (memória da sessão + mensagem)."""

from __future__ import annotations

import json
import re
from typing import Any


class ChatEmailPreferenceService:
    _PERSISTENT_MARKERS = (
        r"\bdaqui\s+pra\s+frente\b",
        r"\bde\s+agora\s+em\s+diante\b",
        r"\bsempre\b",
        r"\bnas\s+pr[oó]ximas\b",
    )

    _PATTERNS: dict[str, tuple[str, ...]] = {
        "shortEmails": (
            r"\bsempre\b.*\be-?mail\b.*\bcurto",
            r"\be-?mails?\s+curtos?\b",
            r"\bsempre\s+curtos?\b.*\be-?mail",
        ),
        "formalTone": (
            r"\bsempre\b.*\bformal\b",
            r"\btom\s+formal\b.*\be-?mail",
            r"\bsempre\b.*\be-?mail\b.*\bformal",
        ),
        "executiveTone": (
            r"\bsempre\b.*\bexecutiv",
            r"\btom\s+executiv",
            r"\bexecutiv.*\bdiretoria\b",
        ),
        "cordialSuppliers": (
            r"\bfornecedor\b.*\bcordial",
            r"\bcordial\b.*\bfornecedor",
            r"\bsempre\b.*\bcordial\b.*\bfornecedor",
        ),
        "cordialCustomers": (
            r"\bcliente\b.*\bcordial",
            r"\bcordial\b.*\bcliente",
            r"\bsempre\b.*\bcordial\b.*\bcliente",
        ),
        "blankSignature": (
            r"\bsempre\b.*\bassinatura\b.*\bbranco",
            r"\bassinatura\s+em\s+branco\b",
            r"\bdeixe\s+assinatura\b.*\bbranco",
            r"\bsempre\b.*\b\[seu\s+nome\]",
        ),
        "threeSubjects": (
            r"\bsempre\b.*\b3\s+assuntos",
            r"\btr[eê]s\s+opções\s+de\s+assunto",
            r"\bsempre\b.*\bassuntos?\s+alternativ",
        ),
        "copyReady": (
            r"\bpronto\s+para\s+copiar\b",
            r"\bformato\s+pronto\b",
            r"\bsempre\b.*\bpronto\s+para\s+copiar",
        ),
    }

    _LABELS: dict[str, str] = {
        "shortEmails": "E-mails curtos",
        "formalTone": "Tom formal",
        "executiveTone": "Tom executivo",
        "cordialSuppliers": "Cordial com fornecedores",
        "cordialCustomers": "Cordial com clientes",
        "blankSignature": "Assinatura em branco",
        "threeSubjects": "3 opções de assunto",
        "copyReady": "Pronto para copiar",
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
        email_context = "e-mail" in normalized or "email" in normalized or "comunicado" in normalized

        for key, patterns in cls._PATTERNS.items():
            if any(re.search(pattern, normalized) for pattern in patterns):
                if persistent or email_context or key in {
                    "shortEmails",
                    "formalTone",
                    "executiveTone",
                    "blankSignature",
                    "threeSubjects",
                    "copyReady",
                }:
                    prefs[key] = True

        return prefs

    @classmethod
    def _load_from_working_memory(cls, working_memory: dict | None) -> dict[str, bool]:
        prefs: dict[str, bool] = {}

        if not working_memory:
            return prefs

        stored = working_memory.get("emailPreferences")

        if isinstance(stored, dict):
            prefs.update({key: bool(value) for key, value in stored.items()})

        behavior = working_memory.get("behaviorInstructions") or {}

        if isinstance(behavior, dict):
            prefs.update(cls._parse_email_writing_behavior(behavior.get("emailWriting")))

        return prefs

    @classmethod
    def _parse_email_writing_behavior(cls, raw: Any) -> dict[str, bool]:
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

        lines = ["Preferências de e-mail nesta sessão:"]

        if prefs.get("shortEmails"):
            lines.append("- Mantenha e-mails curtos e diretos.")
        if prefs.get("formalTone"):
            lines.append("- Use tom formal cordial por padrão.")
        if prefs.get("executiveTone"):
            lines.append("- Use tom executivo para liderança/diretoria.")
        if prefs.get("cordialSuppliers"):
            lines.append("- Use tom cordial com fornecedores.")
        if prefs.get("cordialCustomers"):
            lines.append("- Use tom cordial e cuidadoso com clientes.")
        if prefs.get("blankSignature"):
            lines.append("- Deixe assinatura apenas como [Seu nome], sem inventar cargo.")
        if prefs.get("threeSubjects"):
            lines.append("- Quando pedirem assunto, ofereça 3 opções numeradas.")
        if prefs.get("copyReady"):
            lines.append("- Entregue texto limpo, pronto para copiar (assunto + corpo).")

        return "\n".join(lines)

    @classmethod
    def merge_into_behavior(
        cls,
        message: str | None,
        behavior: dict[str, str] | None,
    ) -> dict[str, str]:
        merged = dict(behavior or {})
        existing = cls._parse_email_writing_behavior(merged.get("emailWriting"))
        incoming = cls._detect_from_message(message)
        combined = {**existing, **incoming}

        if not combined:
            return merged

        merged["emailWriting"] = json.dumps(combined, ensure_ascii=False)

        normalized = (message or "").lower()

        if any(re.search(pattern, normalized) for pattern in cls._PERSISTENT_MARKERS):
            merged["scope"] = merged.get("scope") or "session"

        return merged

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None = None) -> dict:
        prefs = cls.detect(message, working_memory=snapshot)
        snapshot["emailPreferences"] = prefs
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
                    "kind": "emailPreference",
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
