"""Subintenções e contexto para escrita de e-mails corporativos (chat base)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatEmailIntentService:
    @classmethod
    def _email_markers(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.markers()

    @classmethod
    def _subtype_patterns(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.subtypes()

    @classmethod
    def _tone_patterns(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.tones()

    @classmethod
    def _audience_patterns(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.audiences()

    @classmethod
    def _signature_explicit(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.compile_pattern("signatureExplicit")

    @classmethod
    def _recipient_for(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.compile_pattern("recipientFor")

    @classmethod
    def _subject_hint(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.compile_pattern("subjectHint")

    @classmethod
    def _subject_from_answer(cls):
        from app.domain.services.chat_email_intent_content_service import (
            ChatEmailIntentContentService,
        )

        return ChatEmailIntentContentService.compile_pattern("subjectFromAnswer")

    @classmethod
    def message_mentions_email(cls, message: str | None) -> bool:
        normalized = (message or "").strip().lower()

        if not normalized:
            return False

        if ChatTextTaskIntentService.classify(message) == "email":
            return True

        return any(pattern.search(normalized) for pattern in cls._email_markers())

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
            patterns = cls._subtype_patterns().get(subtype) or ()
            if any(pattern.search(normalized) for pattern in patterns):
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
        for tone, patterns in cls._tone_patterns().items():
            if any(pattern.search(normalized) for pattern in patterns):
                return tone

        return None

    @classmethod
    def _detect_audience(cls, normalized: str) -> str | None:
        for audience, patterns in cls._audience_patterns().items():
            if any(pattern.search(normalized) for pattern in patterns):
                return audience

        return None

    @classmethod
    def _extract_recipient(cls, text: str) -> str | None:
        match = cls._recipient_for().search(text)

        if not match:
            return None

        name = (match.group(1) or "").strip()

        if len(name) < 2:
            return None

        return name[:80]

    @classmethod
    def _extract_signature(cls, text: str) -> str | None:
        match = cls._signature_explicit().search(text)

        if not match:
            return None

        return (match.group(1) or "").strip()[:200] or None

    @classmethod
    def _extract_subject_hint(cls, text: str) -> str | None:
        match = cls._subject_hint().search(text)

        if not match:
            return None

        hint = (match.group(1) or "").strip()

        return hint[:120] if len(hint) >= 3 else None

    @classmethod
    def _extract_subject_from_answer(cls, answer: str | None) -> str | None:
        if not answer:
            return None

        match = cls._subject_from_answer().search(answer)

        if not match:
            return None

        subject = (match.group(1) or "").strip()

        return subject[:160] if subject else None
