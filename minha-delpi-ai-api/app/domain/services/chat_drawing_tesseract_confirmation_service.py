"""Re-OCR focal Tesseract em regiões fracas antes de escalar DPI/EasyOCR."""

from __future__ import annotations

import os
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
    ExtractionConfidenceResult,
)
from app.domain.services.chat_drawing_extraction_diagnostic_service import (
    ChatDrawingExtractionDiagnosticService,
    ConfirmationPlan,
)
from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService

_BUNDLE = "drawing_stamp"


class ChatDrawingTesseractConfirmationService:
    @classmethod
    def try_improve(
        cls,
        storage_path: str,
        *,
        filename: str,
        pdf_extract: dict[str, Any],
        confidence: ExtractionConfidenceResult,
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        plan = ChatDrawingExtractionDiagnosticService.build_plan(confidence)

        if plan is None:
            return None, []

        max_passes = cls._max_passes()
        runs: list[dict[str, Any]] = []
        current = dict(pdf_extract)
        current_confidence = confidence

        for pass_index in range(max_passes):
            active_plan = (
                plan
                if pass_index == 0
                else ChatDrawingExtractionDiagnosticService.build_plan(current_confidence)
            )

            if active_plan is None:
                break

            improved, run_meta = cls._run_pass(
                storage_path,
                filename=filename,
                pdf_extract=current,
                plan=active_plan,
                pass_index=pass_index,
                score_before=current_confidence.score_percent,
            )
            runs.append(run_meta)

            if improved is None:
                break

            current = improved
            current_confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
                pdf_extract=current,
            )
            runs[-1]["scoreAfter"] = current_confidence.score_percent
            runs[-1]["improved"] = (
                current_confidence.score_percent > int(run_meta.get("scoreBefore") or 0)
            )
            runs[-1]["meetsThreshold"] = current_confidence.meets_threshold

            if current_confidence.meets_threshold:
                break

            if not runs[-1]["improved"]:
                break

        if not runs or not any(run.get("improved") for run in runs):
            return None, runs

        payload = dict(current)
        retry_meta = payload.get("extractionQualityRetry")

        if isinstance(retry_meta, dict):
            payload["extractionQualityRetry"] = {
                **retry_meta,
                "confirmationAttempts": runs,
            }

        return payload, runs

    @classmethod
    def _run_pass(
        cls,
        storage_path: str,
        *,
        filename: str,
        pdf_extract: dict[str, Any],
        plan: ConfirmationPlan,
        pass_index: int,
        score_before: int,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        region_texts, regions_meta = ChatDrawingRegionService.ocr_selected_drawing_regions(
            storage_path,
            plan.regions,
            dpi_multiplier=cls._dpi_multiplier(),
            engines=cls._engines(),
        )

        run_meta: dict[str, Any] = {
            "passIndex": pass_index,
            "scoreBefore": score_before,
            "plan": plan.to_metadata(),
            "regionCharCounts": {
                region: len(str(text or ""))
                for region, text in region_texts.items()
            },
        }

        if not region_texts:
            run_meta["skipped"] = "no_region_text"
            return None, run_meta

        improved = cls._merge_and_reparse(
            pdf_extract,
            region_texts=region_texts,
            regions_meta=regions_meta,
            storage_path=storage_path,
            filename=filename,
        )
        run_meta["scoreAfter"] = None
        run_meta["improved"] = False

        return improved, run_meta

    @classmethod
    def _merge_and_reparse(
        cls,
        pdf_extract: dict[str, Any],
        *,
        region_texts: dict[str, str],
        regions_meta: dict[str, Any],
        storage_path: str,
        filename: str,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_drawing_pdf_extraction_service import (
            ChatDrawingPdfExtractionService,
        )
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )
        from app.domain.services.chat_pdf_text_fusion_service import (
            ChatPdfTextFusionService,
        )

        source = pdf_extract.get("sourceMetadata")

        if not isinstance(source, dict):
            source = {}

        existing_region_texts = dict(source.get("regionTexts") or {})
        existing_regions = dict(source.get("regions") or {})

        for region, text in region_texts.items():
            normalized = str(text or "").strip()

            if not normalized:
                continue

            existing_region_texts[region] = ChatDrawingRegionService.merge_region_ocr_texts(
                str(existing_region_texts.get(region) or ""),
                normalized,
            )
            region_meta = regions_meta.get(region)

            if isinstance(region_meta, dict):
                existing_regions[region] = {
                    **region_meta,
                    "confirmationPass": True,
                }

        fusion_sources: list[dict[str, str]] = []

        for region_name, region_text in existing_region_texts.items():
            token = str(region_text or "").strip()

            if token:
                fusion_sources.append(
                    {
                        "name": f"{region_name}_region",
                        "text": token,
                    }
                )

        annotation_text = str(source.get("annotationText") or "").strip()

        if annotation_text:
            fusion_sources.append({"name": "annotation", "text": annotation_text})

        embedded = source.get("embedded")

        if isinstance(embedded, dict):
            native_text = str(source.get("nativeText") or "").strip()

            if native_text:
                fusion_sources.append({"name": "fitz_embedded", "text": native_text})

        min_embedded = ChatDocumentVisionContentService.pdf_fusion_min_embedded_chars()
        fused = ChatPdfTextFusionService.fuse(
            fusion_sources,
            min_embedded_chars=min_embedded,
        )
        full_text = str(fused.get("fullText") or "").strip()

        if not full_text:
            full_text = "\n\n".join(
                str(existing_region_texts.get(region) or "").strip()
                for region in ("stamp", "title", "bom", "dimensions")
                if str(existing_region_texts.get(region) or "").strip()
            ).strip()

        if not full_text:
            return None

        stages = [
            str(stage).strip()
            for stage in (source.get("stages") or [])
            if str(stage).strip()
        ]

        if "tesseract_confirmation" not in stages:
            stages.append("tesseract_confirmation")

        if "region_ocr" not in stages:
            stages.append("region_ocr")

        metadata = {
            **source,
            "filename": filename or source.get("filename") or "",
            "storagePath": storage_path,
            "regionTexts": existing_region_texts,
            "regions": existing_regions,
            "stages": stages,
            "extractor": "tesseract_confirmation",
        }

        if existing_region_texts.get("stamp"):
            metadata["stampText"] = existing_region_texts["stamp"]

        if existing_region_texts.get("dimensions"):
            metadata["dimensionsText"] = existing_region_texts["dimensions"]

        return ChatDrawingPdfExtractionService.parse_from_text(
            full_text,
            metadata=metadata,
            storage_path=storage_path,
        )

    @classmethod
    def _config(cls) -> dict[str, Any]:
        retry = ChatAssistantContentService.get_node(_BUNDLE, "extractionQualityRetry")

        if not isinstance(retry, dict):
            return {}

        confirmation = retry.get("confirmation")

        return dict(confirmation) if isinstance(confirmation, dict) else {}

    @classmethod
    def _max_passes(cls) -> int:
        raw = cls._config().get("maxPasses", 2)

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def _dpi_multiplier(cls) -> float:
        raw = cls._config().get("dpiMultiplier", 1.5)

        try:
            return max(1.0, float(raw))
        except (TypeError, ValueError):
            return 1.5

    @classmethod
    def _engines(cls) -> tuple[str, ...]:
        raw = cls._config().get("engines")

        if not isinstance(raw, list) or not raw:
            return ("tesseract",)

        resolved = tuple(
            str(item).strip().lower()
            for item in raw
            if str(item).strip()
        )

        return resolved or ("tesseract",)
