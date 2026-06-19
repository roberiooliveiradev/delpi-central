"""Motores OCR plugáveis para regiões rasterizadas de PDF (desenho)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_pdf_region_ocr_fusion_service import (
    ChatPdfRegionOcrFusionService,
)


class ChatPdfRegionOcrEngineService:
    _easyocr_readers: dict[tuple[str, ...], Any] = {}

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
        region: str | None = None,
    ) -> dict[str, Any]:
        by_engine: dict[str, str] = {}
        code_tokens_by_engine: dict[str, list[dict[str, Any]]] = {}
        engines_run: list[str] = []
        normalized_region = str(region or "").strip().lower()

        for engine in cls._engines_for_region(normalized_region):
            detail = cls._run_engine_detailed(
                engine,
                image,
                lang=lang,
                tesseract_config=tesseract_config,
            )
            text = str(detail.get("text") or "").strip()

            if not text:
                continue

            by_engine[engine] = text
            code_tokens_by_engine[engine] = list(detail.get("codeTokens") or [])
            engines_run.append(engine)

        if normalized_region == "bom":
            fused = ChatPdfRegionOcrFusionService.fuse_bom(
                by_engine,
                code_tokens_by_engine=code_tokens_by_engine,
            )
            fusion = "bom_weighted"
        else:
            fused = ChatPdfRegionOcrFusionService.fuse(by_engine.values())
            fusion = "merge_unique_lines"

        return {
            "text": fused,
            "engines": engines_run,
            "byEngine": by_engine,
            "codeTokensByEngine": code_tokens_by_engine,
            "engine": cls._engine_label(engines_run),
            "fusion": fusion,
        }

    @classmethod
    def _engines_for_region(cls, region: str) -> tuple[str, ...]:
        if region == "bom":
            return ChatDocumentVisionContentService.pdf_bom_region_ocr_engines()

        return cls.enabled_engines()

    @classmethod
    def _engine_label(cls, engines: list[str]) -> str:
        if not engines:
            return "none"

        if len(engines) == 1:
            return engines[0]

        return "+".join(engines)

    @classmethod
    def _run_engine_detailed(
        cls,
        engine: str,
        image: Any,
        *,
        lang: str,
        tesseract_config: str,
    ) -> dict[str, Any]:
        if engine == "tesseract":
            return cls._tesseract_detailed(
                image,
                lang=lang,
                tesseract_config=tesseract_config,
            )

        if engine == "easyocr":
            return cls._easyocr_detailed(image, lang=lang)

        if engine == "paddleocr":
            text = cls._paddleocr(image)
            return {
                "text": text,
                "codeTokens": cls._extract_code_tokens(text),
            }

        return {"text": "", "codeTokens": []}

    @classmethod
    def _extract_code_tokens(
        cls,
        text: str,
        line_confidences: dict[int, float] | None = None,
    ) -> list[dict[str, Any]]:
        pattern = ChatDrawingPatternsService.component_code()
        tokens: list[dict[str, Any]] = []

        for line_index, line in enumerate(str(text or "").splitlines()):
            confidence = float((line_confidences or {}).get(line_index, 1.0))

            for code_index, match in enumerate(pattern.finditer(line)):
                code = str(match.group(1) or "").strip()

                if not code:
                    continue

                tokens.append(
                    {
                        "code": code,
                        "confidence": confidence,
                        "lineIndex": line_index,
                        "codeIndex": code_index,
                    }
                )

        return tokens

    @classmethod
    def _tesseract_detailed(
        cls,
        image: Any,
        *,
        lang: str,
        tesseract_config: str,
    ) -> dict[str, Any]:
        try:
            import pytesseract
            from pytesseract import Output
        except ImportError:
            return {"text": "", "codeTokens": []}

        try:
            kwargs: dict[str, Any] = {
                "lang": lang,
                "output_type": Output.DICT,
            }
            config = str(tesseract_config or "").strip()

            if config:
                kwargs["config"] = config

            data = pytesseract.image_to_data(image, **kwargs)
            line_words: dict[tuple[int, int, int], list[tuple[str, float]]] = {}

            for index, word in enumerate(data.get("text") or []):
                token = str(word or "").strip()

                if not token:
                    continue

                try:
                    confidence = float(data["conf"][index])
                except (TypeError, ValueError, KeyError):
                    confidence = -1.0

                if confidence < 0:
                    continue

                key = (
                    int(data["block_num"][index]),
                    int(data["par_num"][index]),
                    int(data["line_num"][index]),
                )
                line_words.setdefault(key, []).append((token, confidence / 100.0))

            lines: list[str] = []
            line_confidences: dict[int, float] = {}

            for line_index, (_key, words) in enumerate(sorted(line_words.items())):
                line_text = " ".join(token for token, _confidence in words).strip()

                if not line_text:
                    continue

                confidences = [value for _token, value in words if value > 0]
                lines.append(line_text)
                line_confidences[line_index] = (
                    sum(confidences) / len(confidences) if confidences else 1.0
                )

            text = "\n".join(lines).strip()
            return {
                "text": text,
                "codeTokens": cls._extract_code_tokens(text, line_confidences),
            }
        except Exception:
            return {"text": "", "codeTokens": []}

    @classmethod
    def _easyocr_model_dir(cls) -> str | None:
        import os

        raw = os.environ.get("CHAT_EASYOCR_MODEL_DIR", "").strip()
        return raw or None

    @classmethod
    def _easyocr_reader(cls, languages: list[str]) -> Any:
        import easyocr

        key = tuple(languages)
        cached = cls._easyocr_readers.get(key)

        if cached is not None:
            return cached

        kwargs: dict[str, Any] = {"gpu": False, "verbose": False}
        model_dir = cls._easyocr_model_dir()

        if model_dir:
            kwargs["model_storage_directory"] = model_dir

        reader = easyocr.Reader(list(key), **kwargs)
        cls._easyocr_readers[key] = reader
        return reader

    @classmethod
    def _easyocr_detailed(cls, image: Any, *, lang: str) -> dict[str, Any]:
        try:
            import numpy as np
        except ImportError:
            return {"text": "", "codeTokens": []}

        try:
            import easyocr  # noqa: F401
        except ImportError:
            return {"text": "", "codeTokens": []}

        try:
            languages = cls._easyocr_languages(lang)
            reader = cls._easyocr_reader(languages)
            array = np.array(image.convert("RGB"))
            chunks = reader.readtext(array, detail=1, paragraph=False)
            lines: list[str] = []
            line_confidences: dict[int, float] = {}

            for line_index, item in enumerate(chunks):
                if not isinstance(item, (list, tuple)) or len(item) < 3:
                    continue

                text = str(item[1] or "").strip()
                confidence = float(item[2] or 0.0)

                if not text:
                    continue

                lines.append(text)
                line_confidences[line_index] = confidence if confidence > 0 else 1.0

            merged = "\n".join(lines).strip()
            return {
                "text": merged,
                "codeTokens": cls._extract_code_tokens(merged, line_confidences),
            }
        except Exception:
            return {"text": "", "codeTokens": []}

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
