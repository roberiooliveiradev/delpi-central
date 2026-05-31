"""Validação pós-geração de rascunhos de e-mail corporativo."""

from __future__ import annotations

import re
from typing import Any


class ChatEmailQualityValidator:
    _ARTIFICIAL_PHRASES = (
        "estou em consideração",
        "venho por meio deste, venho por meio deste",
        "venho por meio deste",
        "sua participação é vital",
        "a ia pode revolucionar",
        "garantirá eficiência",
        "revolucionar o mercado",
    )

    _WEAK_SUBJECT_PATTERNS = (
        re.compile(r"solicitação\s+de\s+criação", re.I),
        re.compile(r"solicitação\s+de\s+avaliação\s+sobre\s+criação", re.I),
    )

    _INVENTED_SIGNATURE_MARKERS = (
        re.compile(r"roberto\s+silva", re.I),
        re.compile(r"superadministrador", re.I),
        re.compile(r"minha\s+delpi\s+chat\s*$", re.I | re.M),
    )

    _PLACEHOLDER_SIGNATURE = re.compile(
        r"\[(?:seu\s+nome|nome)(?:\s*,\s*cargo[^\]]*)?\]",
        re.I,
    )

    @classmethod
    def validate(
        cls,
        answer: str | None,
        *,
        user_message: str | None = None,
        expected_tone: str | None = None,
        user_provided_signature: str | None = None,
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        checks: list[dict[str, Any]] = []
        passed = True

        def add_check(
            criterion: str,
            ok: bool,
            *,
            detail: str | None = None,
        ) -> None:
            nonlocal passed

            if not ok:
                passed = False

            checks.append(
                {
                    "criterion": criterion,
                    "ok": bool(ok),
                    "detail": detail,
                }
            )

        has_subject = bool(re.search(r"(?im)^\s*assunto\s*:", text))
        add_check("subject_present", has_subject or "assunto" not in (user_message or "").lower())

        add_check(
            "objective_early",
            cls._objective_in_opening(text),
            detail=None if cls._objective_in_opening(text) else "objetivo não evidente no início",
        )

        add_check(
            "natural_language",
            not cls._has_artificial_phrase(text),
            detail="frase artificial detectada" if cls._has_artificial_phrase(text) else None,
        )

        invented_sig = cls._invented_signature(text, user_provided_signature)
        add_check(
            "signature_not_invented",
            not invented_sig,
            detail="possível assinatura inventada" if invented_sig else None,
        )

        add_check(
            "signature_placeholder_or_explicit",
            cls._safe_signature(text, user_provided_signature),
            detail=None,
        )

        add_check(
            "no_unbacked_deadlines",
            not cls._invented_deadline(text, user_message),
            detail="prazo possivelmente inventado" if cls._invented_deadline(text, user_message) else None,
        )

        add_check(
            "explicit_request",
            cls._has_clear_request(text),
            detail=None if cls._has_clear_request(text) else "pedido ao destinatário pouco explícito",
        )

        if expected_tone:
            add_check("tone_compatible", True)

        weak_subject = cls._weak_subject(text)
        add_check(
            "subject_quality",
            not weak_subject,
            detail="assunto genérico ou rígido" if weak_subject else None,
        )

        return {
            "passed": passed,
            "checks": checks,
            "warnings": [c["detail"] for c in checks if not c["ok"] and c.get("detail")],
        }

    @classmethod
    def sanitize(
        cls,
        answer: str | None,
        *,
        user_provided_signature: str | None = None,
    ) -> tuple[str, list[str]]:
        text = (answer or "").strip()
        fixes: list[str] = []

        if not text or user_provided_signature:
            return text, fixes

        if cls._invented_signature(text, None):
            text = cls._replace_invented_signature_tail(text)
            fixes.append("signature_placeholder")

        for phrase in cls._ARTIFICIAL_PHRASES[:3]:
            if phrase in text.lower():
                replacement = {
                    "estou em consideração": "Gostaria de solicitar sua avaliação",
                    "venho por meio deste": "Gostaria de",
                }.get(phrase)

                if replacement:
                    text = re.sub(re.escape(phrase), replacement, text, flags=re.I)
                    fixes.append("artificial_phrase_replaced")

        return text.strip(), fixes

    @classmethod
    def build_remediation_hints(cls, quality: dict[str, Any]) -> list[str]:
        if quality.get("passed"):
            return []

        hints: list[str] = []

        for warning in quality.get("warnings") or []:
            lowered = str(warning).lower()

            if "artificial" in lowered:
                hints.append("Evite frases artificiais; use abertura direta («Gostaria de…»).")
            elif "assinatura" in lowered:
                hints.append("Use [Seu nome] se o remetente não foi informado.")
            elif "assunto" in lowered:
                hints.append("Prefira assunto objetivo (ex.: «Proposta de…»).")
            elif "prazo" in lowered:
                hints.append("Não inclua prazos que o usuário não informou.")

        return hints

    @classmethod
    def _has_artificial_phrase(cls, text: str) -> bool:
        lowered = text.lower()

        return any(phrase in lowered for phrase in cls._ARTIFICIAL_PHRASES)

    @classmethod
    def _invented_signature(
        cls,
        text: str,
        user_provided_signature: str | None,
    ) -> bool:
        if user_provided_signature:
            return False

        tail = text[-400:] if len(text) > 400 else text

        return any(pattern.search(tail) for pattern in cls._INVENTED_SIGNATURE_MARKERS)

    @classmethod
    def _safe_signature(
        cls,
        text: str,
        user_provided_signature: str | None,
    ) -> bool:
        if user_provided_signature and user_provided_signature.lower() in text.lower():
            return True

        if cls._PLACEHOLDER_SIGNATURE.search(text):
            return True

        if "atenciosamente" in text.lower() and not cls._invented_signature(text, None):
            return True

        return bool(user_provided_signature)

    @classmethod
    def _objective_in_opening(cls, text: str) -> bool:
        body = re.sub(r"(?is)^\s*assunto\s*:.*?\n+", "", text).strip()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

        if not paragraphs:
            return False

        opening = " ".join(paragraphs[:2]).lower()

        markers = (
            "gostaria de",
            "precisamos",
            "poderia",
            "convido",
            "apresentar",
            "solicitar",
            "compartilhar",
            "informar",
        )

        return any(marker in opening for marker in markers)

    @classmethod
    def _has_clear_request(cls, text: str) -> bool:
        lowered = text.lower()

        return any(
            token in lowered
            for token in (
                "gostaria de",
                "poderia",
                "precisamos",
                "fico à disposição",
                "fico a disposição",
                "aguardo",
                "próximos passos",
                "proximos passos",
                "avaliação",
                "avaliacao",
                "confirmação",
                "confirmacao",
            )
        )

    @classmethod
    def _weak_subject(cls, text: str) -> bool:
        match = re.search(r"(?im)^\s*assunto\s*:\s*(.+?)\s*$", text)

        if not match:
            return False

        subject = (match.group(1) or "").strip()

        return any(pattern.search(subject) for pattern in cls._WEAK_SUBJECT_PATTERNS)

    @classmethod
    def _replace_invented_signature_tail(cls, text: str) -> str:
        lowered = text.lower()
        marker = "atenciosamente"

        idx = lowered.rfind(marker)

        if idx < 0:
            return text

        head = text[: idx + len(marker)]
        return f"{head},\n\n[Seu nome]"

    @classmethod
    def _invented_deadline(cls, text: str, user_message: str | None) -> bool:
        deadline_in_answer = re.search(
            r"\b(?:até|ate)\s+(?:segunda|terça|terca|quarta|quinta|sexta|"
            r"\d{1,2}/\d{1,2}|\d{1,2}\s+de\s+\w+)",
            text,
            re.I,
        )

        if not deadline_in_answer:
            return False

        user_text = (user_message or "").lower()

        return not re.search(
            r"\b(?:até|ate|prazo|sexta|segunda|terça|terca|quarta|quinta)\b",
            user_text,
        )
