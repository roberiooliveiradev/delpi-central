"""Retentativas de extração PDF até confiança ≥ limiar (Onda 15.7)."""

from __future__ import annotations

import gc
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

            remaining = len(attempts[:max_attempts]) - index - 1

            if remaining > 0:
                if not cls._should_schedule_next_attempt(history=history):
                    selected = best or result

                    return cls._attach_retry_metadata(
                        selected.pdf_extract,
                        history=history,
                        selected=selected,
                        target=target,
                        stopped_reason="no_improvement",
                    )

                cls._release_extraction_memory()

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

        engines_override = cls._resolve_region_ocr_engines(attempt)

        from app.domain.services.chat_pdf_region_ocr_engine_service import (
            ChatPdfRegionOcrEngineService,
        )

        with ChatPdfRegionOcrEngineService.region_ocr_engines_override(engines_override):
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
    def _resolve_region_ocr_engines(
        cls,
        attempt: dict[str, Any] | None,
    ) -> list[str] | None:
        """Motores OCR do loop de retry — default Tesseract-only (sem EasyOCR/PyTorch)."""
        if isinstance(attempt, dict):
            per_attempt = attempt.get("regionOcrEngines")

            if isinstance(per_attempt, list) and per_attempt:
                return [
                    str(item).strip().lower()
                    for item in per_attempt
                    if str(item).strip()
                ]

        loop_default = cls._loop_region_ocr_engines()

        return list(loop_default) if loop_default else None

    @classmethod
    def _loop_region_ocr_engines(cls) -> tuple[str, ...] | None:
        raw = cls._retry_config().get("regionOcrEngines")

        if not isinstance(raw, list) or not raw:
            return ("tesseract",)

        resolved = [
            str(item).strip().lower()
            for item in raw
            if str(item).strip()
        ]

        return tuple(resolved) if resolved else ("tesseract",)

    @classmethod
    def _should_schedule_next_attempt(
        cls,
        *,
        history: list[ExtractionQualityAttemptResult],
    ) -> bool:
        if not history:
            return False

        latest = history[-1]

        if latest.confidence.meets_threshold:
            return False

        if len(history) >= 2 and cls._attempt_stalled(history[-2], latest):
            return False

        return latest.confidence.score < cls._target_confidence()

    @classmethod
    def _release_extraction_memory(cls) -> None:
        if not cls._release_memory_between_attempts():
            return

        from app.domain.services.chat_pdf_region_ocr_engine_service import (
            ChatPdfRegionOcrEngineService,
        )

        ChatPdfRegionOcrEngineService.release_cached_readers()
        gc.collect()

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

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
            "regionOcrEngines": list(cls._loop_region_ocr_engines() or ("tesseract",)),
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
            return max(1, int(raw if raw is not None else 2))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def _release_memory_between_attempts(cls) -> bool:
        return bool(cls._retry_config().get("releaseMemoryBetweenAttempts", True))

    @classmethod
    def _attempt_profiles(cls) -> list[dict[str, Any]]:
        items = cls._retry_config().get("attempts")

        if isinstance(items, list) and items:
            return [dict(item) for item in items if isinstance(item, dict)]

        return [
            {"id": "standard", "enableRegionOcr": None},
            {
                "id": "high_dpi_tesseract",
                "enableRegionOcr": True,
                "regionOcrDpiMultiplier": 1.5,
            },
        ]
