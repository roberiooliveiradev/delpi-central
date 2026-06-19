"""Retentativas de extração PDF até confiança ≥ limiar (Onda 15.7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
    ExtractionConfidenceResult,
)
from app.domain.services.chat_drawing_page_layout_analysis_service import (
    ChatDrawingPageLayoutAnalysisService,
)

_BUNDLE = "drawing_stamp"


@dataclass(frozen=True)
class ExtractionQualityAttemptResult:
    attempt_id: str
    attempt_index: int
    pdf_extract: dict[str, Any]
    confidence: ExtractionConfidenceResult

    def to_metadata(self) -> dict[str, Any]:
        return {
            "attemptId": self.attempt_id,
            "attemptIndex": self.attempt_index,
            "scorePercent": self.confidence.score_percent,
            "meetsThreshold": self.confidence.meets_threshold,
            "components": self.confidence.to_metadata().get("components") or {},
        }


class ChatDrawingExtractionQualityRetryService:
    @classmethod
    def extract_until_confident(
        cls,
        storage_path: str,
        *,
        filename: str = "",
    ) -> dict[str, Any]:
        if not cls._enabled():
            return cls._extract_once(storage_path, filename=filename, attempt=None)

        target = cls._target_confidence()
        max_attempts = cls._max_attempts()
        attempts = cls._attempt_profiles()
        history: list[ExtractionQualityAttemptResult] = []
        best: ExtractionQualityAttemptResult | None = None

        for index, profile in enumerate(attempts[:max_attempts]):
            attempt_id = str(profile.get("id") or f"attempt_{index + 1}")
            pdf_extract = cls._extract_once(
                storage_path,
                filename=filename,
                attempt=profile,
            )
            confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
                pdf_extract=pdf_extract,
            )
            result = ExtractionQualityAttemptResult(
                attempt_id=attempt_id,
                attempt_index=index,
                pdf_extract=pdf_extract,
                confidence=confidence,
            )
            history.append(result)

            if best is None or cls._attempt_is_better(
                candidate=result,
                current_best=best,
            ):
                best = result

            if confidence.meets_threshold:
                return cls._attach_retry_metadata(
                    pdf_extract,
                    history=history,
                    selected=result,
                    target=target,
                    stopped_reason="target_reached",
                )

            if index >= 1 and cls._attempt_stalled(history[-2], result):
                selected = best or result

                return cls._attach_retry_metadata(
                    selected.pdf_extract,
                    history=history,
                    selected=selected,
                    target=target,
                    stopped_reason="no_improvement",
                )

        assert best is not None

        return cls._attach_retry_metadata(
            best.pdf_extract,
            history=history,
            selected=best,
            target=target,
            stopped_reason="max_attempts",
        )

    @classmethod
    def _extract_once(
        cls,
        storage_path: str,
        *,
        filename: str,
        attempt: dict[str, Any] | None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_drawing_pdf_extraction_service import (
            ChatDrawingPdfExtractionService,
        )

        layout_enabled = None

        if isinstance(attempt, dict) and "layoutAnalysisEnabled" in attempt:
            layout_enabled = bool(attempt.get("layoutAnalysisEnabled"))

        with ChatDrawingPageLayoutAnalysisService.layout_analysis_override(layout_enabled):
            return ChatDrawingPdfExtractionService._extract_single_pass(
                storage_path,
                filename=filename,
                extraction_options=cls._build_extraction_options(attempt),
            )

    @classmethod
    def _build_extraction_options(cls, attempt: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(attempt, dict):
            return {}

        options: dict[str, Any] = {}

        if "enableRegionOcr" in attempt:
            raw = attempt.get("enableRegionOcr")

            if raw is not None:
                options["enableRegionOcr"] = bool(raw)

        if attempt.get("regionOcrDpiMultiplier") is not None:
            try:
                options["regionOcrDpiMultiplier"] = float(attempt["regionOcrDpiMultiplier"])
            except (TypeError, ValueError):
                pass

        return options

    @classmethod
    def _attempt_stalled(
        cls,
        previous: ExtractionQualityAttemptResult,
        current: ExtractionQualityAttemptResult,
    ) -> bool:
        if current.confidence.score > previous.confidence.score:
            return False

        prev_codes = len(previous.pdf_extract.get("componentCodes") or [])
        curr_codes = len(current.pdf_extract.get("componentCodes") or [])

        return (
            current.confidence.score <= previous.confidence.score
            and curr_codes <= prev_codes
        )

    @classmethod
    def _attempt_is_better(
        cls,
        *,
        candidate: ExtractionQualityAttemptResult,
        current_best: ExtractionQualityAttemptResult,
    ) -> bool:
        if candidate.confidence.score > current_best.confidence.score:
            return True

        if candidate.confidence.score < current_best.confidence.score:
            return False

        candidate_codes = len(candidate.pdf_extract.get("componentCodes") or [])
        best_codes = len(current_best.pdf_extract.get("componentCodes") or [])

        if candidate_codes != best_codes:
            return candidate_codes > best_codes

        candidate_chars = int(candidate.pdf_extract.get("charCount") or 0)
        best_chars = int(current_best.pdf_extract.get("charCount") or 0)

        return candidate_chars > best_chars

    @classmethod
    def _attach_retry_metadata(
        cls,
        pdf_extract: dict[str, Any],
        *,
        history: list[ExtractionQualityAttemptResult],
        selected: ExtractionQualityAttemptResult,
        target: float,
        stopped_reason: str,
    ) -> dict[str, Any]:
        payload = dict(pdf_extract)
        payload["extractionQualityRetry"] = {
            "targetConfidence": round(target, 4),
            "targetConfidencePercent": int(round(target * 100)),
            "stoppedReason": stopped_reason,
            "attemptCount": len(history),
            "selectedAttemptId": selected.attempt_id,
            "selectedAttemptIndex": selected.attempt_index,
            "selectedScorePercent": selected.confidence.score_percent,
            "meetsTarget": selected.confidence.meets_threshold,
            "attempts": [item.to_metadata() for item in history],
            "selectedConfidence": selected.confidence.to_metadata(),
        }
        return payload

    @classmethod
    def _retry_config(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "extractionQualityRetry")

        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def _enabled(cls) -> bool:
        return bool(cls._retry_config().get("enabled", True))

    @classmethod
    def _target_confidence(cls) -> float:
        raw = cls._retry_config().get("targetConfidence")

        try:
            return float(raw if raw is not None else 0.95)
        except (TypeError, ValueError):
            return 0.95

    @classmethod
    def _max_attempts(cls) -> int:
        raw = cls._retry_config().get("maxAttempts")

        try:
            return max(1, int(raw if raw is not None else 5))
        except (TypeError, ValueError):
            return 5

    @classmethod
    def _attempt_profiles(cls) -> list[dict[str, Any]]:
        items = cls._retry_config().get("attempts")

        if isinstance(items, list) and items:
            return [dict(item) for item in items if isinstance(item, dict)]

        return [
            {"id": "standard", "enableRegionOcr": None},
            {"id": "forced_region_ocr", "enableRegionOcr": True},
            {"id": "high_dpi_regions", "enableRegionOcr": True, "regionOcrDpiMultiplier": 1.75},
            {
                "id": "static_layout_regions",
                "enableRegionOcr": True,
                "layoutAnalysisEnabled": False,
            },
            {
                "id": "high_dpi_static_layout",
                "enableRegionOcr": True,
                "regionOcrDpiMultiplier": 2.0,
                "layoutAnalysisEnabled": False,
            },
        ]
