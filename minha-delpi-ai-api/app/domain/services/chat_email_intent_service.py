"""Subintenções e contexto para escrita de e-mails corporativos (chat base)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatEmailIntentService:
    _EMAIL_MARKERS = (
        r"\be-?mail\b",
        r"\be-?mail\s+anterior\b",
        r"\bcomunicado\s+por\s+e-?mail\b",
        r"\bmensagem\s+formal\b",
        r"\bresponda\s+este\s+e-?mail\b",
        r"\bmelhore\s+este\s+e-?mail\b",
        r"\brevise\s+este\s+e-?mail\b",
    )

    _SUBTYPE_PATTERNS: dict[str, tuple[str, ...]] = {
        "email_reply": (
            r"\brespond(a|er)\b.*\be-?mail",
            r"\bresponda\s+este\s+e-?mail",
            r"\bresposta\s+.*\be-?mail",
        ),
        "email_rewrite": (
            r"\bmelhor(e|ar)\b.*\be-?mail",
            r"\brevise\b.*\be-?mail",
            r"\breescrev.*\be-?mail",
            r"\be-?mail\s+anterior\b",
            r"\breescrev.*\banterior\b",
        ),
        "email_correct": (
            r"\bcorrig.*\be-?mail",
            r"\bortografia\b.*\be-?mail",
        ),
        "email_shorten": (
            r"\bdeixe\b.*\bmais\s+curto",
            r"\bmais\s+curto\b",
            r"\bencurte\b",
            r"\bresuma\s+o\s+e-?mail",
        ),
        "email_formalize": (
            r"\bdeixe\b.*\bmais\s+formal",
            r"\bmais\s+formal\b",
            r"\bformalize\b",
        ),
        "email_soften": (
            r"\bdeixe\b.*\bmais\s+cordial",
            r"\bmais\s+cordial\b",
            r"\bmais\s+educad",
        ),
        "email_firm": (
            r"\bdeixe\b.*\bmais\s+firme",
            r"\bmais\s+firme\b",
            r"\btom\s+mais\s+firme",
        ),
        "email_subjects": (
            r"\bassunto\s+alternativ",
            r"\bcrie\s+assunto",
            r"\bopções\s+de\s+assunto",
            r"\bopcoes\s+de\s+assunto",
            r"\b3\s+assuntos\b",
        ),
        "email_translate": (
            r"\btraduza\b.*\be-?mail",
            r"\btraduzir\b.*\be-?mail",
            r"\bpasse\s+para\s+ingl",
        ),
        "email_create": (
            r"\bescrev(a|er)\b",
            r"\bredij(a|ir)\b",
            r"\bcrie\b",
            r"\bmonte\b",
            r"\bfaça\s+um\s+e-?mail",
            r"\bfaca\s+um\s+e-?mail",
            r"\bcomunicado\b",
            r"\bcobrança\b",
            r"\bcobranca\b",
        ),
    }

    _TONE_PATTERNS: dict[str, tuple[str, ...]] = {
        "formal": (r"\bformal\b", r"\bprezado\b"),
        "executive": (r"\bexecutiv", r"\bdiretoria\b", r"\bliderança\b", r"\blideranca\b"),
        "cordial": (r"\bcordial\b", r"\beducad", r"\bpor\s+gentileza\b"),
        "firm": (r"\bfirme\b", r"\burgente\b", r"\bcobrança\b", r"\bcobranca\b"),
        "direct": (r"\bcurto\b", r"\bdireto\b", r"\bobjetiv"),
    }

    _AUDIENCE_PATTERNS: dict[str, tuple[str, ...]] = {
        "supplier": (r"\bfornecedor\b",),
        "customer": (r"\bcliente\b",),
        "internal": (r"\bequipe\b", r"\bcolega\b", r"\binterno\b"),
    }

    _SIGNATURE_EXPLICIT = re.compile(
        r"(?:assine\s+como|assinatura[:\s]+|assinar\s+como)\s+(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )

    _RECIPIENT_FOR = re.compile(
        r"(?:para|ao|à|a)\s+(?:o\s+|a\s+)?([A-ZÁÉÍÓÚÂÊÔÃÇ][\wáéíóúâêôãç\s]{2,40}?)(?:\s+sobre|\s+referente|,|\.|$)",
        re.IGNORECASE,
    )

    @classmethod
    def message_mentions_email(cls, message: str | None) -> bool:
        normalized = (message or "").strip().lower()

        if not normalized:
            return False

        if ChatTextTaskIntentService.classify(message) == "email":
            return True

        return any(re.search(pattern, normalized) for pattern in cls._EMAIL_MARKERS)

    @classmethod
    def is_email_writing(cls, message: str | None) -> bool:
        if not cls.message_mentions_email(message):
            return False

        return cls.classify_subtype(message) is not None or ChatTextTaskIntentService.classify(
            message
        ) in {"email", "write", "rewrite", "tone_adjust", "translate", "message"}

    @classmethod
    def classify_subtype(cls, message: str | None) -> str | None:
        normalized = (message or "").strip().lower()

        if len(normalized) < 4:
            return None

        if not cls.message_mentions_email(message):
            if ChatTextTaskIntentService.classify(message) not in {
                "email",
                "write",
                "rewrite",
            }:
                return None

        ordered = (
            "email_reply",
            "email_translate",
            "email_subjects",
            "email_correct",
            "email_shorten",
            "email_formalize",
            "email_soften",
            "email_firm",
            "email_rewrite",
            "email_create",
        )

        for subtype in ordered:
            patterns = cls._SUBTYPE_PATTERNS.get(subtype) or ()
            if any(re.search(pattern, normalized) for pattern in patterns):
                return subtype

        if ChatTextTaskIntentService.classify(message) == "email":
            return "email_create"

        if cls.message_mentions_email(message):
            return "email_create"

        return None

    @classmethod
    def extract_context(cls, message: str | None) -> dict[str, Any]:
        text = (message or "").strip()
        normalized = text.lower()
        subtype = cls.classify_subtype(message)
        tone = cls._detect_tone(normalized)
        audience = cls._detect_audience(normalized)
        recipient = cls._extract_recipient(text)
        signature = cls._extract_signature(text)
        subject_hint = cls._extract_subject_hint(text)

        missing: list[str] = []

        if not recipient and subtype in {"email_create", "email_reply"}:
            missing.append("recipient")

        if not signature:
            missing.append("senderName")

        return {
            "type": "email",
            "subtype": subtype,
            "recipient": recipient,
            "tone": tone,
            "audience": audience,
            "subjectHint": subject_hint,
            "senderSignature": signature,
            "missingFields": missing,
            "inventedFieldsPrevented": True,
        }

    @classmethod
    def build_text_task_metadata(
        cls,
        *,
        message: str | None,
        answer: str | None = None,
    ) -> dict[str, Any] | None:
        if not cls.is_email_writing(message):
            return None

        ctx = cls.extract_context(message)
        subject = cls._extract_subject_from_answer(answer)

        if subject:
            ctx["subject"] = subject

        ctx["suggestions"] = [
            "Deixar mais formal",
            "Deixar mais curto",
            "Tom mais executivo",
            "Tom mais cordial",
            "Tom mais firme",
            "Criar assunto alternativo",
        ]

        return {"textTask": ctx}

    @classmethod
    def _detect_tone(cls, normalized: str) -> str | None:
        for tone, patterns in cls._TONE_PATTERNS.items():
            if any(re.search(pattern, normalized) for pattern in patterns):
                return tone

        return None

    @classmethod
    def _detect_audience(cls, normalized: str) -> str | None:
        for audience, patterns in cls._AUDIENCE_PATTERNS.items():
            if any(re.search(pattern, normalized) for pattern in patterns):
                return audience

        return None

    @classmethod
    def _extract_recipient(cls, text: str) -> str | None:
        match = cls._RECIPIENT_FOR.search(text)

        if not match:
            return None

        name = (match.group(1) or "").strip()

        if len(name) < 2:
            return None

        return name[:80]

    @classmethod
    def _extract_signature(cls, text: str) -> str | None:
        match = cls._SIGNATURE_EXPLICIT.search(text)

        if not match:
            return None

        return (match.group(1) or "").strip()[:200] or None

    @classmethod
    def _extract_subject_hint(cls, text: str) -> str | None:
        match = re.search(
            r"(?:assunto|sobre|referente\s+a)\s*[:\-]?\s*(.+?)(?:\.|$)",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        hint = (match.group(1) or "").strip()

        return hint[:120] if len(hint) >= 3 else None

    @classmethod
    def _extract_subject_from_answer(cls, answer: str | None) -> str | None:
        if not answer:
            return None

        match = re.search(
            r"(?im)^\s*assunto\s*:\s*(.+?)\s*$",
            answer,
        )

        if not match:
            return None

        subject = (match.group(1) or "").strip()

        return subject[:160] if subject else None
