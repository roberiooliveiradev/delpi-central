"""Extração estruturada de desenhos técnicos em PDF — Onda 12.2."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.infrastructure.config.settings import Settings

_REV_PATTERN = re.compile(
    r"(?:REV(?:IS[AÃ]O)?\.?|REVISION)\s*[:.]?\s*(\d{1,3})",
    re.IGNORECASE,
)
class ChatDrawingPdfExtractionService:
    @classmethod
    def max_pages(cls) -> int:
        return max(1, int(Settings.CHAT_DRAWING_PDF_MAX_PAGES))

    @classmethod
    def extract_from_storage_path(cls, storage_path: str, *, filename: str = "") -> dict[str, Any]:
        from app.application.services.chat_attachment_text_extractor import (
            ChatAttachmentTextExtractor,
        )

        extracted = ChatAttachmentTextExtractor().extract(
            storage_path=storage_path,
            filename=filename or Path(storage_path).name,
            content_type="application/pdf",
        )

        if not extracted.get("supported"):
            return cls._empty(
                reason=str((extracted.get("metadata") or {}).get("reason") or "unsupported"),
            )

        text = str(extracted.get("content") or "").strip()

        return cls.parse_from_text(
            text,
            metadata=extracted.get("metadata") if isinstance(extracted.get("metadata"), dict) else {},
        )

    @classmethod
    def parse_from_attachment_context(cls, attachment_context: str | None) -> dict[str, Any] | None:
        if not attachment_context or not str(attachment_context).strip():
            return None

        blocks = str(attachment_context).split("###")

        merged = ""

        for block in blocks[1:]:
            lines = block.strip().splitlines()

            if len(lines) <= 1:
                continue

            merged += "\n".join(lines[1:]) + "\n\n"

        if not merged.strip():
            merged = str(attachment_context)

        parsed = cls.parse_from_text(merged.strip())

        if parsed.get("productCode") or parsed.get("legible"):
            return parsed

        return None

    @classmethod
    def parse_from_text(
        cls,
        text: str,
        *,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        normalized = str(text or "").strip()
        char_count = len(normalized)

        product_code = ChatProductQueryIntentService.extract_product_code(normalized)

        if not product_code:
            match = re.search(r"\b(90\d{6}|50\d{6}|10\d{6}|100\d{5})\b", normalized)

            if match:
                product_code = ChatProductQueryIntentService.normalize_product_code(
                    match.group(1)
                )

        revision = cls._extract_revision(normalized)
        customer_reference = cls._extract_labeled_value(
            normalized,
            labels=("COD. CLIENTE", "COD CLIENTE", "CÓD. CLIENTE", "REFERENCIA CLIENTE"),
        )
        description = cls._extract_labeled_value(
            normalized,
            labels=("DESCRIÇÃO", "DESCRICAO", "DESCRIPTION"),
        )

        min_chars = max(1, int(Settings.CHAT_DRAWING_PDF_MIN_LEGIBLE_CHARS))
        legible = char_count >= min_chars and bool(product_code or revision)

        payload: dict[str, Any] = {
            "productCode": product_code,
            "revision": revision,
            "customerReference": customer_reference,
            "description": description,
            "charCount": char_count,
            "legible": legible,
            "extractor": (metadata or {}).get("extractor") or "text_parse",
        }

        if metadata:
            payload["sourceMetadata"] = metadata

        return payload

    @classmethod
    def _extract_revision(cls, text: str) -> str | None:
        match = _REV_PATTERN.search(text)

        if match:
            return match.group(1).zfill(2)

        return None

    @classmethod
    def _extract_labeled_value(cls, text: str, *, labels: tuple[str, ...]) -> str | None:
        upper = text.upper()

        for label in labels:
            idx = upper.find(label)

            if idx < 0:
                continue

            snippet = text[idx : idx + 120]
            parts = re.split(r"[:|\n]", snippet, maxsplit=1)

            if len(parts) < 2:
                continue

            value = parts[1].strip().split("\n", 1)[0].strip()

            if value:
                return value[:80]

        return None

    @classmethod
    def _empty(cls, *, reason: str) -> dict[str, Any]:
        return {
            "productCode": None,
            "revision": None,
            "customerReference": None,
            "description": None,
            "charCount": 0,
            "legible": False,
            "extractor": reason,
        }
