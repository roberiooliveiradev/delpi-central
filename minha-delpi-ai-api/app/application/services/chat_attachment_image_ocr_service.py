"""OCR opcional em anexos de imagem (Playbook 07)."""

from __future__ import annotations

import os
from pathlib import Path

from app.infrastructure.config.settings import Settings


class ChatAttachmentImageOcrService:
    @classmethod
    def is_enabled(cls) -> bool:
        from app.application.services.chat_platform_runtime_access import vision_settings

        return bool(vision_settings().get("attachmentImageOcrEnabled"))

    @classmethod
    def try_extract_text(cls, path: Path) -> dict:
        if not cls.is_enabled():
            return {
                "text": None,
                "used": False,
                "reason": "disabled",
            }

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            return {
                "text": None,
                "used": False,
                "reason": "dependencies_unavailable",
                "error": exc.__class__.__name__,
            }

        lang = os.getenv("CHAT_ATTACHMENT_IMAGE_OCR_LANG", "por+eng").strip() or "por+eng"
        max_chars = Settings.CHAT_ATTACHMENT_IMAGE_OCR_MAX_CHARS

        try:
            with Image.open(path) as image:
                rgb = image.convert("RGB")
                raw = pytesseract.image_to_string(rgb, lang=lang)
        except Exception as exc:
            return {
                "text": None,
                "used": False,
                "reason": "ocr_failed",
                "error": exc.__class__.__name__,
            }

        text = " ".join(str(raw or "").split()).strip()

        if not text:
            return {
                "text": None,
                "used": True,
                "reason": "no_text_detected",
            }

        if len(text) > max_chars:
            text = f"{text[: max_chars - 1]}…"

        return {
            "text": text,
            "used": True,
            "reason": None,
            "charCount": len(text),
            "lang": lang,
        }
