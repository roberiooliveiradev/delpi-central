"""Plano de confirmação focal — regiões a re-OCR quando confiança < limiar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ExtractionConfidenceResult,
)

_BUNDLE = "drawing_stamp"
_REGION_ORDER = ("stamp", "title", "bom", "dimensions")


@dataclass(frozen=True)
class ConfirmationPlan:
    regions: tuple[str, ...]
    reasons: tuple[str, ...]
    weak_components: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "regions": list(self.regions),
            "reasons": list(self.reasons),
            "weakComponents": list(self.weak_components),
        }


class ChatDrawingExtractionDiagnosticService:
    @classmethod
    def build_plan(cls, confidence: ExtractionConfidenceResult) -> ConfirmationPlan | None:
        if not cls._enabled():
            return None

        if confidence.meets_threshold:
            return None

        config = cls._config()
        component_regions = config.get("componentRegions")
        reason_regions = config.get("reasonRegions")

        if not isinstance(component_regions, dict):
            component_regions = {}

        if not isinstance(reason_regions, dict):
            reason_regions = {}

        planned: list[str] = []
        weak_components: list[str] = []

        for component, score in confidence.components.items():
            if float(score) >= float(confidence.threshold):
                continue

            weak_components.append(str(component))

            for region in component_regions.get(component, []):
                token = str(region).strip().lower()

                if token:
                    planned.append(token)

        for reason in confidence.reasons:
            for region in reason_regions.get(reason, []):
                token = str(region).strip().lower()

                if token:
                    planned.append(token)

        ordered = cls._dedupe_regions(planned)

        if not ordered:
            return None

        return ConfirmationPlan(
            regions=tuple(ordered),
            reasons=confidence.reasons,
            weak_components=tuple(weak_components),
        )

    @classmethod
    def _dedupe_regions(cls, regions: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        for region in _REGION_ORDER:
            if region in regions and region not in seen:
                ordered.append(region)
                seen.add(region)

        for region in regions:
            if region not in seen:
                ordered.append(region)
                seen.add(region)

        return ordered

    @classmethod
    def _config(cls) -> dict[str, Any]:
        retry = ChatAssistantContentService.get_node(_BUNDLE, "extractionQualityRetry")

        if not isinstance(retry, dict):
            return {}

        confirmation = retry.get("confirmation")

        return dict(confirmation) if isinstance(confirmation, dict) else {}

    @classmethod
    def _enabled(cls) -> bool:
        return bool(cls._config().get("enabled", True))
