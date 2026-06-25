"""Configuração e gates — visão de documentos."""

from __future__ import annotations

import base64
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.config.settings import Settings

from app.application.services.chat_document_vision.document_vision_runtime import vision_runtime


class ChatDocumentVisionConfigService:
    @classmethod
    def is_enabled(cls) -> bool:
        return bool(vision_runtime().get("documentVisionEnabled"))

    @classmethod
    def auto_vlm_fallback_enabled(cls) -> bool:
        return bool(
            vision_runtime().get("documentVisionAutoVlmFallback")
            and Settings.CHAT_DOCUMENT_VISION_OLLAMA_MODEL
        )

    @classmethod
    def image_describe_enabled(cls) -> bool:
        return bool(
            vision_runtime().get("documentVisionImageDescribeEnabled")
            and Settings.CHAT_DOCUMENT_VISION_OLLAMA_MODEL
        )

    @classmethod
    def is_pdf(cls, content_type: str, filename: str, storage_path: str) -> bool:
        lowered = f"{content_type} {filename} {storage_path}".lower()
        return "pdf" in lowered or lowered.endswith(".pdf")

    @classmethod
    def is_image(cls, content_type: str, filename: str) -> bool:
        lowered = f"{content_type} {filename}".lower()
        return any(
            token in lowered
            for token in (
                "image/png",
                "image/jpeg",
                "image/jpg",
                "image/webp",
                "image/tiff",
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".tif",
                ".tiff",
            )
        )

    @classmethod
    def is_vision_target(cls, content_type: str | None, filename: str, storage_path: str) -> bool:
        content_type = str(content_type or "")
        filename = str(filename or "")

        return cls.is_pdf(content_type, filename, storage_path) or cls.is_image(
            content_type,
            filename,
        )

    @classmethod
    def default_content_type(cls, filename: str) -> str:
        lowered = str(filename or "").lower()

        if lowered.endswith(".pdf"):
            return "application/pdf"

        if lowered.endswith(".png"):
            return "image/png"

        if lowered.endswith(".webp"):
            return "image/webp"

        if lowered.endswith((".jpg", ".jpeg")):
            return "image/jpeg"

        return "application/octet-stream"

    @classmethod
    def should_replace_attachment_content(cls, extracted: str, ocr_text: str) -> bool:
        normalized = str(extracted or "").strip()

        if not normalized:
            return True

        placeholders = (
            "Conteúdo visual indexado por metadados",
            "descreva o que precisa",
            "texto alternativo",
        )

        if any(token in normalized for token in placeholders):
            return True

        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))

        return len(normalized) < min_legible and len(ocr_text) >= min_legible
