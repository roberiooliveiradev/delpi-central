from __future__ import annotations

import os
import tempfile
from pathlib import Path

from app.config import settings


class PacEvidenceImageOcrService:
    @classmethod
    def is_enabled(cls) -> bool:
        return bool(settings.PAC_EVIDENCE_OCR_ENABLED)

    @classmethod
    def extract_text_from_bytes(
        cls,
        content: bytes,
        *,
        mime_type: str | None = None,
    ) -> dict:
        normalized = (mime_type or "").lower()
        if not normalized.startswith("image/"):
            return {"text": None, "used": False, "reason": "not_image"}

        if not cls.is_enabled():
            return {"text": None, "used": False, "reason": "disabled"}

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

        lang = (settings.PAC_EVIDENCE_OCR_LANG or "por+eng").strip() or "por+eng"
        suffix = ".png" if "png" in normalized else ".jpg"
        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(content)
                temp_path = Path(handle.name)

            with Image.open(temp_path) as image:
                raw = pytesseract.image_to_string(image.convert("RGB"), lang=lang)
        except Exception as exc:
            return {
                "text": None,
                "used": False,
                "reason": "ocr_failed",
                "error": exc.__class__.__name__,
            }
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

        text = " ".join(str(raw or "").split()).strip()
        if not text:
            return {"text": None, "used": True, "reason": "no_text_detected", "lang": lang}

        max_chars = settings.PAC_EVIDENCE_OCR_MAX_CHARS
        if len(text) > max_chars:
            text = f"{text[: max_chars - 1]}…"

        return {
            "text": text,
            "used": True,
            "reason": None,
            "charCount": len(text),
            "lang": lang,
        }
