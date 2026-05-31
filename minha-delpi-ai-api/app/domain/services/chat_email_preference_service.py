"""Preferências persistentes de escrita de e-mail (memória da sessão + mensagem)."""

from __future__ import annotations

import re
from typing import Any


class ChatEmailPreferenceService:
    _PATTERNS: dict[str, tuple[str, ...]] = {
        "shortEmails": (r"\bsempre\b.*\be-?mail\b.*\bcurto", r"\be-?mails?\s+curtos?\b"),
        "formalTone": (r"\bsempre\b.*\bformal\b", r"\btom\s+formal\b.*\be-?mail"),
        "executiveTone": (r"\bsempre\b.*\bexecutiv", r"\btom\s+executiv"),
        "cordialSuppliers": (r"\bfornecedor\b.*\bcordial", r"\bcordial\b.*\bfornecedor"),
        "blankSignature": (
            r"\bsempre\b.*\bassinatura\b.*\bbranco",
            r"\bassinatura\s+em\s+branco\b",
            r"\bdeixe\s+assinatura\b.*\bbranco",
        ),
        "threeSubjects": (r"\bsempre\b.*\b3\s+assuntos", r"\btr[eê]s\s+opções\s+de\s+assunto"),
        "copyReady": (r"\bpronto\s+para\s+copiar\b", r"\bformato\s+pronto\b"),
    }

    @classmethod
    def detect(
        cls,
        message: str | None,
        *,
        working_memory: dict | None = None,
    ) -> dict[str, bool]:
        prefs: dict[str, bool] = {}
        sources = [message or ""]

        behavior = (working_memory or {}).get("behaviorInstructions") or {}

        if isinstance(behavior, dict):
            email_behavior = behavior.get("emailWriting")

            if isinstance(email_behavior, dict):
                prefs.update({key: bool(value) for key, value in email_behavior.items()})

        for prior in ((working_memory or {}).get("emailPreferences") or {},):
            if isinstance(prior, dict):
                prefs.update({key: bool(value) for key, value in prior.items()})

        for text in sources:
            normalized = (text or "").strip().lower()

            if not normalized:
                continue

            for key, patterns in cls._PATTERNS.items():
                if prefs.get(key):
                    continue

                if any(re.search(pattern, normalized) for pattern in patterns):
                    prefs[key] = True

        return prefs

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
        prefs = cls.detect(message)

        if not prefs:
            return merged

        import json

        merged["emailWriting"] = json.dumps(prefs, ensure_ascii=False)

        if any(
            token in (message or "").lower()
            for token in ("sempre", "daqui pra frente", "de agora em diante")
        ):
            merged["scope"] = merged.get("scope") or "session"

        return merged
