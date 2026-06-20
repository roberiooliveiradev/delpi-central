"""Guarda de memória para OCR pesado (EasyOCR / PyTorch) — evita OOM silencioso."""

from __future__ import annotations

import gc
from typing import Any

from app.domain.exceptions.vision_exceptions import VisionMemoryLimitedError
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatVisionMemoryGuardService:
    @classmethod
    def available_memory_mb(cls) -> int | None:
        try:
            with open("/proc/meminfo", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("MemAvailable:"):
                        kb = int(line.split()[1])
                        return max(0, kb // 1024)
        except (OSError, ValueError, IndexError):
            return None

        return None

    @classmethod
    def min_available_mb_for_easyocr(cls) -> int:
        return ChatDocumentVisionContentService.memory_guard_min_mb_for_easyocr()

    @classmethod
    def min_available_mb_for_drawing_ocr(cls) -> int:
        return ChatDocumentVisionContentService.memory_guard_min_mb_for_drawing_ocr()

    @classmethod
    def easyocr_lazy_release_enabled(cls) -> bool:
        return ChatDocumentVisionContentService.memory_guard_easyocr_lazy_release()

    @classmethod
    def can_use_easyocr(cls) -> bool:
        required = cls.min_available_mb_for_easyocr()
        available = cls.available_memory_mb()

        if available is None:
            return True

        return available >= required

    @classmethod
    def can_run_drawing_region_ocr(cls) -> bool:
        required = cls.min_available_mb_for_drawing_ocr()
        available = cls.available_memory_mb()

        if available is None:
            return True

        return available >= required

    @classmethod
    def ensure_easyocr_headroom(cls) -> None:
        if cls.can_use_easyocr():
            return

        available = cls.available_memory_mb()
        raise VisionMemoryLimitedError(
            f"easyocr_blocked_available_{available}mb_required_{cls.min_available_mb_for_easyocr()}mb"
        )

    @classmethod
    def filter_engines_for_memory(cls, engines: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        resolved = cls._normalize_engines(engines)

        if cls.can_use_easyocr():
            return resolved

        filtered = tuple(engine for engine in resolved if engine != "easyocr")
        return filtered or ("tesseract",)

    @classmethod
    def release_ocr_memory(cls) -> None:
        from app.domain.services.chat_pdf_region_ocr_engine_service import (
            ChatPdfRegionOcrEngineService,
        )

        ChatPdfRegionOcrEngineService.release_cached_readers()
        gc.collect()

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    @classmethod
    def is_memory_related_error(cls, exc: BaseException | None) -> bool:
        if exc is None:
            return False

        if isinstance(exc, (MemoryError, VisionMemoryLimitedError)):
            return True

        token = str(exc).strip().lower()

        return any(
            marker in token
            for marker in (
                "out of memory",
                "memory limited",
                "cannot allocate",
                "easyocr_blocked",
                "vision_memory_limited",
            )
        )

    @classmethod
    def attach_memory_limited_metadata(cls, payload: dict[str, Any]) -> dict[str, Any]:
        merged = dict(payload)
        merged["memoryLimited"] = True
        merged["memoryAvailableMb"] = cls.available_memory_mb()
        return merged

    @classmethod
    def _normalize_engines(cls, engines: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        resolved: list[str] = []

        for engine in engines:
            token = str(engine or "").strip().lower()

            if token and token not in resolved:
                resolved.append(token)

        return tuple(resolved or ("tesseract",))
