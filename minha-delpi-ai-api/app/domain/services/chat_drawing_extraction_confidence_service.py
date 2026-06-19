"""Confiança composta da leitura PDF/OCR — gate assertivo antes de reprovar por PDF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


@dataclass(frozen=True)
class ExtractionConfidenceResult:
    score: float
    threshold: float
    meets_threshold: bool
    components: dict[str, float]
    reasons: tuple[str, ...]

    @property
    def score_percent(self) -> int:
        return int(round(self.score * 100))

    @property
    def threshold_percent(self) -> int:
        return int(round(self.threshold * 100))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "scorePercent": self.score_percent,
            "threshold": round(self.threshold, 4),
            "thresholdPercent": self.threshold_percent,
            "meetsThreshold": self.meets_threshold,
            "components": {
                key: round(value, 4) for key, value in sorted(self.components.items())
            },
            "reasons": list(self.reasons),
        }


class ChatDrawingExtractionConfidenceService:
    _COMPONENT_DEFAULT = 1.0

    @classmethod
    def evaluate_for_extraction(
        cls,
        *,
        pdf_extract: dict[str, Any] | None,
    ) -> ExtractionConfidenceResult:
        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        threshold = cls._extraction_target_confidence()
        components: dict[str, float] = {}
        reasons: list[str] = []

        components["legibility"] = cls._legibility_for_extraction(pdf_meta, reasons)
        components["stamp"] = cls._stamp_component_for_extraction(pdf_meta, reasons)
        components["bom_scope"] = cls._bom_scope_component(pdf_meta, reasons)
        components["ocr_regions"] = cls._ocr_regions_component(pdf_meta, reasons)
        components["bom_completeness"] = cls._bom_completeness_component(pdf_meta, reasons)
        components["dimensions"] = cls._dimensions_extraction_component(pdf_meta, reasons)

        score = min(components.values()) if components else 0.0

        return ExtractionConfidenceResult(
            score=score,
            threshold=threshold,
            meets_threshold=score >= threshold,
            components=components,
            reasons=tuple(reasons),
        )

    @classmethod
    def _extraction_target_confidence(cls) -> float:
        from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

        node = ChatAssistantContentService.get_node("drawing_stamp", "extractionQualityRetry") or {}

        if not isinstance(node, dict):
            node = {}

        raw = node.get("targetConfidence", 0.95)

        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.95

    @classmethod
    def _legibility_for_extraction(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        component_count = len(pdf_meta.get("componentCodes") or [])
        char_count = int(pdf_meta.get("charCount") or 0)

        if pdf_meta.get("legible") and component_count >= 4 and char_count >= 200:
            return 0.96

        return cls._legibility_component(pdf_meta, reasons)

    @classmethod
    def _stamp_component_for_extraction(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        title_block = pdf_meta.get("titleBlock")
        product_code = str(pdf_meta.get("productCode") or "").strip()
        revision = str(pdf_meta.get("revision") or pdf_meta.get("internalRevision") or "").strip()

        if isinstance(title_block, dict) and title_block:
            return 1.0

        if product_code and revision:
            return 0.96

        if product_code:
            return ChatDrawingPatternsService.extraction_confidence_code_only_stamp()

        return cls._stamp_component(pdf_meta, reasons)

    @classmethod
    def _bom_completeness_component(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        components = pdf_meta.get("componentCodes") or []
        intermediates = pdf_meta.get("intermediateCodes") or []

        if isinstance(components, list) and isinstance(intermediates, list):
            if components and intermediates:
                return 1.0

            if components:
                reasons.append("intermediate_codes_missing")
                return ChatDrawingPatternsService.extraction_confidence_bom_scope_partial()

        reasons.append("component_codes_missing")
        return ChatDrawingPatternsService.extraction_confidence_bom_scope_missing()

    @classmethod
    def _dimensions_extraction_component(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        dimensions = pdf_meta.get("dimensions")

        if not isinstance(dimensions, dict):
            reasons.append("dimensions_missing")
            return ChatDrawingPatternsService.extraction_confidence_segment_pending()

        has_segments = bool(dimensions.get("segmentLengthsMm"))
        has_decape = dimensions.get("leftDecapeMm") is not None or dimensions.get("rightDecapeMm") is not None
        has_length = dimensions.get("totalLengthMm") is not None

        if has_segments and has_decape:
            return 1.0

        if has_length or has_decape or has_segments:
            reasons.append("dimensions_partial")
            return ChatDrawingPatternsService.extraction_confidence_dimension_ambiguous()

        reasons.append("dimensions_missing")
        return ChatDrawingPatternsService.extraction_confidence_segment_pending()

    @classmethod
    def evaluate(
        cls,
        *,
        pdf_extract: dict[str, Any] | None,
        items: list[dict[str, Any]] | None = None,
    ) -> ExtractionConfidenceResult:
        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        checklist = [item for item in (items or []) if isinstance(item, dict)]
        threshold = ChatDrawingPatternsService.extraction_confidence_threshold()
        components: dict[str, float] = {}
        reasons: list[str] = []

        components["legibility"] = cls._legibility_component(pdf_meta, reasons)
        components["stamp"] = cls._stamp_component(pdf_meta, reasons)
        components["bom_scope"] = cls._bom_scope_component(pdf_meta, reasons)
        components["ocr_regions"] = cls._ocr_regions_component(pdf_meta, reasons)
        components["dimensions"] = cls._dimensions_component(checklist, reasons)
        components["bom_reading"] = cls._bom_reading_component(checklist, reasons)

        score = min(components.values()) if components else 0.0

        return ExtractionConfidenceResult(
            score=score,
            threshold=threshold,
            meets_threshold=score >= threshold,
            components=components,
            reasons=tuple(reasons),
        )

    @classmethod
    def _legibility_component(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        vision = pdf_meta.get("documentVision")

        if not isinstance(vision, dict):
            vision = {}

        raw = vision.get("legibilityScore")

        if raw is None and pdf_meta.get("legible"):
            raw = 0.85

        try:
            legibility = float(raw if raw is not None else 0.35)
        except (TypeError, ValueError):
            legibility = 0.35

        if not vision.get("hasTitleBlock"):
            capped = min(legibility, ChatDrawingPatternsService.extraction_confidence_stamp_cap())
            reasons.append("stamp_block_missing")
            return capped

        if legibility < ChatDrawingPatternsService.extraction_confidence_threshold():
            reasons.append("legibility_below_threshold")

        return max(0.0, min(1.0, legibility))

    @classmethod
    def _stamp_component(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        vision = pdf_meta.get("documentVision")

        if not isinstance(vision, dict):
            vision = {}

        product_code = str(pdf_meta.get("productCode") or "").strip()

        if product_code and vision.get("hasTitleBlock"):
            return 1.0

        if product_code:
            reasons.append("product_code_without_title_block")
            return ChatDrawingPatternsService.extraction_confidence_code_only_stamp()

        reasons.append("product_code_missing")
        return ChatDrawingPatternsService.extraction_confidence_missing_code()

    @classmethod
    def _bom_scope_component(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        scopes = pdf_meta.get("validationScopes")

        if not isinstance(scopes, dict):
            scopes = {}

        bom_scope = scopes.get("bom")

        if isinstance(bom_scope, dict) and bom_scope.get("available"):
            return ChatDrawingPatternsService.extraction_confidence_bom_scope_ok()

        if pdf_meta.get("componentCodes"):
            reasons.append("bom_scope_partial")
            return ChatDrawingPatternsService.extraction_confidence_bom_scope_partial()

        reasons.append("bom_scope_unavailable")
        return ChatDrawingPatternsService.extraction_confidence_bom_scope_missing()

    @classmethod
    def _ocr_regions_component(cls, pdf_meta: dict[str, Any], reasons: list[str]) -> float:
        vision = pdf_meta.get("documentVision")

        if not isinstance(vision, dict):
            vision = {}

        stages = [
            str(stage).strip().lower()
            for stage in (vision.get("stages") or [])
            if str(stage).strip()
        ]
        source_metadata = pdf_meta.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            stages.extend(
                str(stage).strip().lower()
                for stage in (source_metadata.get("stages") or [])
                if str(stage).strip()
            )

        stage_set = set(stages)

        if "region_ocr" in stage_set:
            return ChatDrawingPatternsService.extraction_confidence_region_ocr()

        if any(token in stage_set for token in ("tesseract_pdf", "tesseract_image", "easyocr")):
            reasons.append("ocr_without_regional_bom")
            return ChatDrawingPatternsService.extraction_confidence_page_ocr_only()

        reasons.append("embedded_text_only")
        return ChatDrawingPatternsService.extraction_confidence_embedded_only()

    @classmethod
    def _dimensions_component(
        cls,
        checklist: list[dict[str, Any]],
        reasons: list[str],
    ) -> float:
        score = cls._COMPONENT_DEFAULT

        for item in checklist:
            template_key = str(item.get("templateKey") or "").strip()
            status = str(item.get("status") or "").strip()

            if template_key in {"segment_length_pending", "segment_lengths_consolidated"}:
                score = min(
                    score,
                    ChatDrawingPatternsService.extraction_confidence_segment_pending(),
                )
                reasons.append("segment_length_pending")

            if template_key == "decape_mismatch" and status in {"error", "critical_error"}:
                score = min(
                    score,
                    ChatDrawingPatternsService.extraction_confidence_decape_conflict(),
                )
                reasons.append("decape_mismatch")

            if template_key == "dimension_note_ambiguous" and status == "pending":
                score = min(
                    score,
                    ChatDrawingPatternsService.extraction_confidence_dimension_ambiguous(),
                )
                reasons.append("dimension_note_ambiguous")

        return score

    @classmethod
    def _bom_reading_component(
        cls,
        checklist: list[dict[str, Any]],
        reasons: list[str],
    ) -> float:
        score = cls._COMPONENT_DEFAULT
        pdf_dependent_keys = ChatDrawingPatternsService.extraction_confidence_pdf_conflict_keys()

        for item in checklist:
            template_key = str(item.get("templateKey") or "").strip()
            status = str(item.get("status") or "").strip()

            if template_key == "balloon_missing_codes" and status == "pending":
                score = min(
                    score,
                    ChatDrawingPatternsService.extraction_confidence_balloon_pending(),
                )
                reasons.append("balloon_missing_codes")

            if template_key in pdf_dependent_keys and status in {"error", "critical_error"}:
                score = min(
                    score,
                    ChatDrawingPatternsService.extraction_confidence_pdf_conflict(),
                )
                reasons.append(f"pdf_conflict:{template_key}")

        return score
