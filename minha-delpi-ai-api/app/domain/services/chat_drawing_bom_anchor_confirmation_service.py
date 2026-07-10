"""Confirmação BOM com códigos esperados do `/analyser` no haystack OCR."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_analyser_anchor_service import AnalyserBomAnchor
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
    ExtractionConfidenceResult,
)
from app.domain.services.chat_drawing_extraction_diagnostic_service import ConfirmationPlan
from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService
from app.domain.services.chat_drawing_tesseract_confirmation_service import (
    ChatDrawingTesseractConfirmationService,
)


class ChatDrawingBomAnchorConfirmationService:
    @classmethod
    def try_improve_with_anchor(
        cls,
        storage_path: str,
        *,
        filename: str,
        pdf_extract: dict[str, Any],
        anchor: AnalyserBomAnchor,
        confidence: ExtractionConfidenceResult | None = None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        if confidence is None:
            confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
                pdf_extract=pdf_extract,
            )

        plan = ConfirmationPlan(
            regions=("bom",),
            reasons=confidence.reasons,
            weak_components=tuple(
                name
                for name, score in confidence.components.items()
                if float(score) < float(confidence.threshold)
            ),
        )

        region_texts, regions_meta = ChatDrawingRegionService.ocr_selected_drawing_regions(
            storage_path,
            plan.regions,
            dpi_multiplier=ChatDrawingTesseractConfirmationService._dpi_multiplier(),
            engines=ChatDrawingTesseractConfirmationService._engines(),
        )

        run_meta: dict[str, Any] = {
            "phase": "analyser_bom_anchor",
            "plan": plan.to_metadata(),
            "anchor": anchor.to_metadata(),
            "scoreBefore": confidence.score_percent,
        }

        if not region_texts.get("bom"):
            run_meta["skipped"] = "no_bom_region_text"
            return None, run_meta

        merged = ChatDrawingTesseractConfirmationService._merge_and_reparse(
            pdf_extract,
            region_texts=region_texts,
            regions_meta=regions_meta,
            storage_path=storage_path,
            filename=filename,
        )

        if merged is None:
            run_meta["skipped"] = "reparse_failed"
            return None, run_meta

        anchored = cls._inject_anchor_presence_codes(
            merged,
            anchor=anchor,
            extra_haystack_texts=tuple(
                str(region_texts.get(region) or "").strip()
                for region in plan.regions
                if str(region_texts.get(region) or "").strip()
            ),
        )
        new_confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
            pdf_extract=anchored,
        )

        run_meta["scoreAfter"] = new_confidence.score_percent
        run_meta["improved"] = new_confidence.score_percent > confidence.score_percent
        run_meta["meetsThreshold"] = new_confidence.meets_threshold
        run_meta["addedCodes"] = list(
            anchored.get("bomAnchorConfirmation", {}).get("addedCodes") or []
        )

        if not run_meta["improved"] and not run_meta["addedCodes"]:
            return None, run_meta

        return anchored, run_meta

    @classmethod
    def _inject_anchor_presence_codes(
        cls,
        pdf_extract: dict[str, Any],
        *,
        anchor: AnalyserBomAnchor,
        extra_haystack_texts: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        from app.domain.services.chat_drawing_bom_comparison_service import (
            ChatDrawingBomComparisonService,
        )

        payload = dict(pdf_extract)
        found = ChatDrawingBomComparisonService.collect_haystack_presence_codes(
            payload,
            api_codes=set(anchor.expected_codes),
        )
        found |= cls._collect_codes_in_texts(
            extra_haystack_texts,
            api_codes=anchor.expected_codes,
        )
        existing = {
            str(code).strip()
            for code in (payload.get("componentCodes") or [])
            if str(code).strip()
        }
        added = sorted(found - existing)

        if added:
            payload["componentCodes"] = sorted(existing | set(found))
            payload["bomAnchorConfirmation"] = {
                "productCode": anchor.product_code,
                "addedCodes": added,
                "expectedCodeCount": len(anchor.expected_codes),
            }

        return payload

    @classmethod
    def _collect_codes_in_texts(
        cls,
        texts: tuple[str, ...],
        *,
        api_codes: frozenset[str],
    ) -> set[str]:
        pattern = ChatDrawingPatternsService.component_code()
        codes: set[str] = set()

        for haystack in texts:
            for match in pattern.finditer(str(haystack or "")):
                code = ChatProductQueryIntentService.normalize_product_code(
                    str(match.group(1) or "")
                )

                if code and code in api_codes:
                    codes.add(code)

        return codes
