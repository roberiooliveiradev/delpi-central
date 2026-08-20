"""Solve de leitura por LLM/VLM após OCR abaixo do limiar (application).

Ordem: OCR/Tesseract → este solve → só então escalação ao usuário.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
)
from app.domain.services.chat_drawing_extraction_user_escalation_service import (
    ChatDrawingExtractionUserEscalationService,
)
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)

logger = logging.getLogger(__name__)


class ChatDrawingExtractionLlmSolveService:
    @classmethod
    def apply_if_needed(
        cls,
        storage_path: str,
        *,
        filename: str = "",
        pdf_extract: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = dict(pdf_extract) if isinstance(pdf_extract, dict) else {}

        if not payload:
            return payload

        confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
            pdf_extract=payload,
        )
        config = ChatDrawingExtractionUserEscalationService.llm_solve_config()

        if not ChatDrawingExtractionUserEscalationService.llm_solve_enabled():
            return cls._attach_meta(
                payload,
                {
                    "attempted": False,
                    "resolved": False,
                    "skippedReason": "disabled",
                    "scoreBefore": confidence.score_percent,
                    "meetsThresholdBefore": confidence.meets_threshold,
                },
            )

        when_below = bool(config.get("whenBelowTarget", True))

        if when_below and confidence.meets_threshold:
            return cls._attach_meta(
                payload,
                {
                    "attempted": False,
                    "resolved": True,
                    "skippedReason": "already_meets_target",
                    "scoreBefore": confidence.score_percent,
                    "meetsThresholdBefore": True,
                },
            )

        score_before = confidence.score_percent
        try:
            improved = cls._run_vlm_solve(
                storage_path,
                filename=filename or Path(storage_path).name,
                pdf_extract=payload,
                config=config,
            )
        except Exception as exc:
            logger.exception(
                "drawing_extraction_llm_solve_failed",
                extra={"error": str(exc)},
            )
            return cls._attach_meta(
                payload,
                {
                    "attempted": True,
                    "resolved": False,
                    "skippedReason": "error",
                    "errorType": type(exc).__name__,
                    "scoreBefore": score_before,
                    "meetsThresholdBefore": False,
                },
            )

        if improved is None:
            return cls._attach_meta(
                payload,
                {
                    "attempted": True,
                    "resolved": False,
                    "skippedReason": "empty_or_unavailable",
                    "scoreBefore": score_before,
                    "meetsThresholdBefore": False,
                },
            )

        after = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
            pdf_extract=improved,
        )

        return cls._attach_meta(
            improved,
            {
                "attempted": True,
                "resolved": after.meets_threshold,
                "scoreBefore": score_before,
                "scoreAfter": after.score_percent,
                "meetsThresholdBefore": False,
                "meetsThresholdAfter": after.meets_threshold,
                "engine": str(improved.get("extractor") or improved.get("engine") or "vlm"),
            },
        )

    @classmethod
    def _run_vlm_solve(
        cls,
        storage_path: str,
        *,
        filename: str,
        pdf_extract: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any] | None:
        from app.application.services.chat_document_vision.chat_document_vision_stage_service import (
            ChatDocumentVisionStageService,
        )
        from app.domain.services.chat_drawing_pdf_extraction_service import (
            ChatDrawingPdfExtractionService,
        )
        from app.domain.services.chat_drawing_region_service import (
            ChatDrawingRegionService,
        )
        from app.domain.services.chat_pdf_text_fusion_service import (
            ChatPdfTextFusionService,
        )

        purpose = str(
            config.get("purpose")
            or ChatDocumentVisionContentService.vision_purpose("ocr")
        ).strip()
        use_regions = bool(config.get("useDrawingRegions", True))
        partial = ChatDocumentVisionStageService._partial_ocr_texts_from_payload(
            pdf_extract
        )
        content_type = "application/pdf"
        stages: list[str] = []
        warnings: list[str] = []

        vlm = ChatDocumentVisionStageService.stage_ollama_vlm(
            storage_path,
            filename=filename,
            content_type=content_type,
            purpose=purpose,
            use_drawing_regions=use_regions,
            partial_ocr_texts=partial,
        )
        warnings.extend(vlm.get("warnings") or [])
        vlm_text = str(vlm.get("fullText") or "").strip()

        if not vlm_text:
            return None

        stages.append("llm_solve_vlm")
        source = pdf_extract.get("sourceMetadata")

        if not isinstance(source, dict):
            source = {}

        region_texts = (
            dict(vlm.get("regionTexts"))
            if isinstance(vlm.get("regionTexts"), dict)
            else {}
        )
        existing_region_texts = dict(source.get("regionTexts") or {})

        for region, text in region_texts.items():
            normalized = str(text or "").strip()

            if not normalized:
                continue

            existing_region_texts[region] = ChatDrawingRegionService.merge_region_ocr_texts(
                str(existing_region_texts.get(region) or ""),
                normalized,
            )

        stamp_text = str(
            vlm.get("stampText") or region_texts.get("stamp") or source.get("stampText") or ""
        ).strip()
        bom_text = str(
            vlm.get("bomText") or region_texts.get("bom") or source.get("bomText") or ""
        ).strip()
        dimensions_text = str(
            region_texts.get("dimensions") or source.get("dimensionsText") or ""
        ).strip()

        fused = ChatPdfTextFusionService.fuse(
            [
                {"name": "ocr_base", "text": str(pdf_extract.get("fullText") or pdf_extract.get("text") or ""), "score": 50},
                {"name": "vlm_solve", "text": vlm_text, "score": 80},
            ],
            min_embedded_chars=ChatDocumentVisionContentService.pdf_fusion_min_embedded_chars(),
        )
        fused_text = str(fused.get("fullText") or "").strip() or vlm_text
        meta = {
            **source,
            "filename": filename,
            "regionTexts": existing_region_texts,
            "stampText": stamp_text or str(source.get("stampText") or ""),
            "bomText": bom_text or str(source.get("bomText") or ""),
            "dimensionsText": dimensions_text or str(source.get("dimensionsText") or ""),
            "vlmSolve": True,
            "vlmRegionsSent": list(vlm.get("vlmRegionsSent") or []),
            "vlmImageCount": int(vlm.get("vlmImageCount") or 0),
            "stages": list(source.get("stages") or []) + stages,
            "warnings": list(source.get("warnings") or []) + warnings,
        }
        parsed = ChatDrawingPdfExtractionService.parse_from_text(
            fused_text,
            metadata=meta,
            storage_path=storage_path,
        )
        merged = dict(pdf_extract)
        merged.update(parsed)
        merged["fullText"] = fused_text
        merged["sourceMetadata"] = meta
        merged["extractor"] = "llm_solve_vlm"
        merged["charCount"] = len(fused_text)

        return merged

    @classmethod
    def _attach_meta(
        cls,
        pdf_extract: dict[str, Any],
        llm_solve: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(pdf_extract)
        retry = payload.get("extractionQualityRetry")

        if not isinstance(retry, dict):
            retry = {}

        retry = dict(retry)
        retry["llmSolve"] = dict(llm_solve)
        payload["extractionQualityRetry"] = retry

        return payload
