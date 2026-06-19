"""Camadas assertivas pós-checklist — confiança da leitura antes de reprovar por PDF."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
    ExtractionConfidenceResult,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


class ChatDrawingValidationAssertionService:
    @classmethod
    def apply(
        cls,
        *,
        items: list[dict[str, Any]],
        pdf_extract: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], ExtractionConfidenceResult | None]:
        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}

        if not pdf_meta:
            return items, None

        confidence = ChatDrawingExtractionConfidenceService.evaluate(
            pdf_extract=pdf_meta,
            items=items,
        )
        adjusted = cls._apply_confidence_gate(items, confidence)
        adjusted = cls._prepend_confidence_item(adjusted, confidence)

        return adjusted, confidence

    @classmethod
    def _apply_confidence_gate(
        cls,
        items: list[dict[str, Any]],
        confidence: ExtractionConfidenceResult,
    ) -> list[dict[str, Any]]:
        if confidence.meets_threshold:
            return items

        pdf_dependent_keys = ChatDrawingPatternsService.validation_pdf_dependent_template_keys()
        demoted_status = ChatDrawingPatternsService.validation_confidence_demoted_status()
        adjusted: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            row = deepcopy(item)
            template_key = str(row.get("templateKey") or "").strip()
            status = str(row.get("status") or "").strip()

            if (
                template_key in pdf_dependent_keys
                and status in ChatDrawingPatternsService.validation_confidence_demotable_statuses()
            ):
                row["status"] = demoted_status
                row["validationLayer"] = {
                    "gate": "extraction_confidence",
                    "fromStatus": status,
                    "scorePercent": confidence.score_percent,
                    "thresholdPercent": confidence.threshold_percent,
                }
                row["recommendation"] = ChatDrawingValidationContentService.format(
                    "validationLayers",
                    "demotedRecommendation",
                    default=(
                        "Conferir manualmente no PDF — confiança da leitura abaixo do limiar"
                    ),
                    score=str(confidence.score_percent),
                    threshold=str(confidence.threshold_percent),
                )

            adjusted.append(row)

        return adjusted

    @classmethod
    def _prepend_confidence_item(
        cls,
        items: list[dict[str, Any]],
        confidence: ExtractionConfidenceResult,
    ) -> list[dict[str, Any]]:
        content = ChatDrawingValidationContentService
        status = "ok" if confidence.meets_threshold else "pending"
        recommendation_field = "recommendationOk" if confidence.meets_threshold else "recommendationPending"

        confidence_item = content.item_from_template(
            "extraction_confidence",
            status=status,
            pdf_evidence=content.evidence_format(
                "extractionConfidenceScore",
                score=str(confidence.score_percent),
                threshold=str(confidence.threshold_percent),
            ),
            api_evidence=content.evidence("dash"),
            recommendation_field=recommendation_field,
        )
        confidence_item["extractionConfidence"] = confidence.to_metadata()

        insert_at = 0

        for index, item in enumerate(items):
            if str(item.get("section") or "") == "PDF":
                insert_at = index
                break
            if str(item.get("section") or "") == "Cabeçalho":
                insert_at = index + 1

        return items[:insert_at] + [confidence_item] + items[insert_at:]
