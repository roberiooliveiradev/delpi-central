"""OCR Tesseract página inteira para PDFs com pouco texto embutido (indexação de anexos)."""

from __future__ import annotations

import os
from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService


class ChatPdfPageTesseractOcrService:
    @classmethod
    def extract_text(
        cls,
        storage_path: str,
        *,
        page_limit: int | None = None,
    ) -> dict[str, Any]:
        try:
            import fitz
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            return {
                "fullText": "",
                "charCount": 0,
                "pageCount": 0,
                "warnings": [f"dependencies_unavailable:{exc.__class__.__name__}"],
            }

        lang = os.getenv("CHAT_DOCUMENT_VISION_TESSERACT_LANG", "por+eng").strip() or "por+eng"
        dpi = max(72, int(ChatDomainConfigService.chat_document_vision_dpi()))
        max_pages = page_limit or ChatDocumentVisionContentService.pdf_attachment_index_max_pages()
        max_pages = max(1, int(max_pages))
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        texts: list[str] = []
        warnings: list[str] = []

        try:
            document = fitz.open(storage_path)
        except Exception as exc:
            return {
                "fullText": "",
                "charCount": 0,
                "pageCount": 0,
                "warnings": [f"pdf_open_failed:{exc.__class__.__name__}"],
            }

        try:
            page_count = min(document.page_count, max_pages)

            if document.page_count > max_pages:
                warnings.append(f"truncated_pages:{document.page_count}>{max_pages}")

            for index in range(page_count):
                page = document.load_page(index)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                raw = pytesseract.image_to_string(image, lang=lang)
                chunk = str(raw or "").strip()

                if chunk:
                    texts.append(chunk)
        finally:
            document.close()

        full_text = "\n\n".join(texts).strip()

        return {
            "fullText": full_text,
            "charCount": len(full_text),
            "pageCount": page_count if "page_count" in locals() else 0,
            "warnings": warnings,
            "engine": "tesseract_page",
        }
