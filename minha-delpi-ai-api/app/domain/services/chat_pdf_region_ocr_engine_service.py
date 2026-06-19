"""Motores OCR plugáveis para regiões rasterizadas de PDF (desenho)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_pdf_region_ocr_fusion_service import (
    ChatPdfRegionOcrFusionService,
)


class ChatPdfRegionOcrEngineService:
    @classmethod
    def enabled_engines(cls) -> tuple[str, ...]:
        configured = ChatDocumentVisionContentService.pdf_region_ocr_engines()
        resolved: list[str] = []

        for engine in configured:
            token = str(engine or "").strip().lower()

            if token and token not in resolved:
                resolved.append(token)

        return tuple(resolved or ("tesseract",))

    @classmethod
    def recognize(
        cls,
        image: Any,
        *,
        lang: str,
        tesseract_config: str = "",
    ) -> dict[str, Any]:
        by_engine: dict[str, str] = {}
        engines_run: list[str] = []

        for engine in cls.enabled_engines():
            text = cls._run_engine(
                engine,
                image,
                lang=lang,
                tesseract_config=tesseract_config,
            )

            if text:
                by_engine[engine] = text
                engines_run.append(engine)

        fused = ChatPdfRegionOcrFusionService.fuse(by_engine.values())

        return {
            "text": fused,
            "engines": engines_run,
            "byEngine": by_engine,
            "engine": cls._engine_label(engines_run),
        }

    @classmethod
    def _engine_label(cls, engines: list[str]) -> str:
        if not engines:
            return "none"

        if len(engines) == 1:
            return engines[0]

        return "+".join(engines)

    @classmethod
    def _run_engine(
        cls,
        engine: str,
        image: Any,
        *,
        lang: str,
        tesseract_config: str,
    ) -> str:
        if engine == "tesseract":
            return cls._tesseract(image, lang=lang, tesseract_config=tesseract_config)

        if engine == "easyocr":
            return cls._easyocr(image, lang=lang)

        if engine == "paddleocr":
            return cls._paddleocr(image)

        return ""

    @classmethod
    def _tesseract(cls, image: Any, *, lang: str, tesseract_config: str) -> str:
        try:
            import pytesseract
        except ImportError:
            return ""

        try:
            kwargs: dict[str, Any] = {"lang": lang}
            config = str(tesseract_config or "").strip()

            if config:
                kwargs["config"] = config

            return str(pytesseract.image_to_string(image, **kwargs) or "").strip()
        except Exception:
            return ""

    @classmethod
    def _easyocr(cls, image: Any, *, lang: str) -> str:
        try:
            import easyocr
            import numpy as np
        except ImportError:
            return ""

        try:
            languages = cls._easyocr_languages(lang)
            reader = easyocr.Reader(languages, gpu=False, verbose=False)
            array = np.array(image.convert("RGB"))
            chunks = reader.readtext(array, detail=0, paragraph=True)
            lines = [str(chunk or "").strip() for chunk in chunks if str(chunk or "").strip()]

            return "\n".join(lines).strip()
        except Exception:
            return ""

    @classmethod
    def _easyocr_languages(cls, lang: str) -> list[str]:
        tokens = [token.strip().lower() for token in str(lang or "").split("+") if token.strip()]
        mapped: list[str] = []

        for token in tokens:
            if token.startswith("por"):
                mapped.append("pt")
            elif token.startswith("eng") or token == "en":
                mapped.append("en")

        return mapped or ["pt", "en"]

    @classmethod
    def _paddleocr(cls, image: Any) -> str:
        try:
            from paddleocr import PaddleOCR
            import numpy as np
        except ImportError:
            return ""

        try:
            engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            array = np.array(image.convert("RGB"))
            result = engine.ocr(array, cls=True)

            if not result:
                return ""

            lines: list[str] = []

            for block in result:
                if not isinstance(block, list):
                    continue

                for item in block:
                    if not isinstance(item, (list, tuple)) or len(item) < 2:
                        continue

                    payload = item[1]

                    if isinstance(payload, (list, tuple)) and payload:
                        text = str(payload[0] or "").strip()
                    else:
                        text = str(payload or "").strip()

                    if text:
                        lines.append(text)

            return "\n".join(lines).strip()
        except Exception:
            return ""
