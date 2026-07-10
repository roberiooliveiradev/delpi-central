"""Âncora BOM a partir do payload `/analyser` para confirmação focal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ExtractionConfidenceResult,
)

_BUNDLE = "drawing_stamp"


@dataclass(frozen=True)
class AnalyserBomAnchor:
    product_code: str
    expected_codes: frozenset[str]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "productCode": self.product_code,
            "expectedCodeCount": len(self.expected_codes),
            "expectedCodes": sorted(self.expected_codes)[:50],
        }


class ChatDrawingAnalyserAnchorService:
    @classmethod
    def build_anchor(
        cls,
        *,
        analyser_root: dict[str, Any] | None,
        product_code: str,
    ) -> AnalyserBomAnchor | None:
        code = str(product_code or "").strip().upper()
        root = analyser_root if isinstance(analyser_root, dict) else {}

        if not code or not root:
            return None

        expected = ChatDrawingBomComparisonService.collect_structure_bom_codes(
            root,
            code,
        )

        if not expected:
            return None

        return AnalyserBomAnchor(
            product_code=code,
            expected_codes=frozenset(expected),
        )

    @classmethod
    def should_anchor_bom(
        cls,
        *,
        pdf_extract: dict[str, Any] | None,
        confidence: ExtractionConfidenceResult | None = None,
        product_code: str | None = None,
    ) -> bool:
        if not cls._enabled():
            return False

        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        resolved_code = str(product_code or pdf_meta.get("productCode") or "").strip()

        if not resolved_code:
            return False

        if confidence is None:
            from app.domain.services.chat_drawing_extraction_confidence_service import (
                ChatDrawingExtractionConfidenceService,
            )

            confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
                pdf_extract=pdf_meta,
            )

        threshold = cls._weak_bom_threshold()

        bom_scope = float(confidence.components.get("bom_scope") or 1.0)
        bom_completeness = float(confidence.components.get("bom_completeness") or 1.0)

        return bom_scope < threshold or bom_completeness < threshold

    @classmethod
    def _config(cls) -> dict[str, Any]:
        retry = ChatAssistantContentService.get_node(_BUNDLE, "extractionQualityRetry")

        if not isinstance(retry, dict):
            return {}

        anchor = retry.get("analyserAnchor")

        return dict(anchor) if isinstance(anchor, dict) else {}

    @classmethod
    def _enabled(cls) -> bool:
        return bool(cls._config().get("enabled", True))

    @classmethod
    def _weak_bom_threshold(cls) -> float:
        raw = cls._config().get("minWeakBomComponentScore", 0.95)

        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.95
