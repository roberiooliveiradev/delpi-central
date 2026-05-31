"""Intenção de leitura de conteúdo em anexos (PDF/imagem) — Onda 13 / Playbook 07."""

from __future__ import annotations

import re


class ChatAttachmentDocumentIntentService:
    _CONTENT_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(
            r"\bo\s+que\s+(?:esta|está|tem)\s+(?:escrito|no|dentro)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:ler|leia|transcrev|resum[ao])\s+(?:o|do|esse|este)\s+"
            r"(?:arquivo|pdf|anexo|documento|boleto)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bconte[uú]do\s+do\s+(?:arquivo|pdf|anexo|documento)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\btexto\s+do\s+(?:arquivo|pdf|anexo|documento)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bo\s+que\s+diz\s+o\s+(?:arquivo|pdf|anexo|documento)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:descrev[ae]|explique)\s+(?:o|do)\s+(?:arquivo|pdf|anexo|documento)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:o\s+que|quais?\s+dados?).{0,40}(?:arquivo|pdf|anexo)\b",
            re.IGNORECASE,
        ),
    )

    @classmethod
    def is_document_content_question(cls, message: str | None) -> bool:
        normalized = str(message or "").strip()

        if len(normalized) < 8:
            return False

        return any(pattern.search(normalized) for pattern in cls._CONTENT_PATTERNS)
