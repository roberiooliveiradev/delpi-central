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
from app.domain.services.chat_vision_memory_guard_service import (
    ChatVisionMemoryGuardService,
)
from app.domain.exceptions.vision_exceptions import VisionMemoryLimitedError

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
        attempt_slots = attempts[:max_attempts]
        history: list[ExtractionQualityAttemptResult] = []
        best: ExtractionQualityAttemptResult | None = None

        for index, profile in enumerate(attempt_slots):
            attempt_id = str(profile.get("id") or f"attempt_{index + 1}")

            if cls._attempt_uses_easyocr(profile) and not ChatVisionMemoryGuardService.can_use_easyocr():
                continue

            try:
                pdf_extract = cls._extract_once(
                    storage_path,
                    filename=filename,
                    attempt=profile,
                )
            except (MemoryError, VisionMemoryLimitedError):
                ChatVisionMemoryGuardService.release_ocr_memory()

                if best is not None:
                    payload = ChatVisionMemoryGuardService.attach_memory_limited_metadata(
                        dict(best.pdf_extract)
                    )

                    return cls._attach_retry_metadata(
                        payload,
                        history=history,
                        selected=best,
                        target=target,
                        stopped_reason="memory_limited",
                    )

                raise
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

            confirmed_payload, _confirmation_runs = (
                cls._try_confirmation_pass(
                    storage_path,
                    filename=filename,
                    pdf_extract=pdf_extract,
                    confidence=confidence,
                    attempt_index=index,
                    history=history,
                )
            )

            if confirmed_payload is not None:
                pdf_extract = confirmed_payload
                confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
                    pdf_extract=pdf_extract,
                )
                result = ExtractionQualityAttemptResult(
                    attempt_id=f"confirm_weak_fields_{index + 1}",
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
                        stopped_reason="confirmation_reached",
                    )

            if (
                best is not None
                and cls._pdf_extract_used_embedded_only(best.pdf_extract)
                and cls._embedded_text_meets_ocr_gate(best.pdf_extract)
                and cls._embedded_bom_extracted(best.pdf_extract)
                and str(best.pdf_extract.get("productCode") or "").strip()
                and index + 1 < len(attempt_slots)
            ):
                return cls._attach_retry_metadata(
                    best.pdf_extract,
                    history=history,
                    selected=best,
                    target=target,
                    stopped_reason="embedded_sufficient",
                )

            if (
                index >= 1
                and cls._attempt_stalled(history[-2], result)
                and best is not None
                and cls._pdf_extract_used_embedded_only(best.pdf_extract)
                and cls._embedded_bom_extracted(best.pdf_extract)
            ):
                return cls._attach_retry_metadata(
                    best.pdf_extract,
                    history=history,
                    selected=best,
                    target=target,
                    stopped_reason="embedded_sufficient",
                )

            if (
                index >= 1
                and cls._attempt_stalled(history[-2], result)
                and len(attempt_slots) - index - 1 > 0
                and not cls._has_distinct_remaining_profiles(
                    history_len=index + 1,
                    attempt_slots=attempt_slots,
                )
            ):
                selected = best or result

                return cls._attach_retry_metadata(
                    selected.pdf_extract,
                    history=history,
                    selected=selected,
                    target=target,
                    stopped_reason="no_improvement",
                )

            remaining = len(attempt_slots) - index - 1

            if remaining > 0:
                if not cls._should_schedule_next_attempt(
                    history=history,
                    attempt_slots=attempt_slots,
                ):
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
        attempt_slots: list[dict[str, Any]] | None = None,
    ) -> bool:
        if not history:
            return False

        latest = history[-1]

        if latest.confidence.meets_threshold:
            return False

        slots = attempt_slots if isinstance(attempt_slots, list) else cls._attempt_profiles()[: cls._max_attempts()]

        if len(history) >= 2 and cls._attempt_stalled(history[-2], latest):
            return cls._has_distinct_remaining_profiles(
                history_len=len(history),
                attempt_slots=slots,
            )

        return latest.confidence.score < cls._target_confidence()

    @classmethod
    def _release_extraction_memory(cls) -> None:
        if not cls._release_memory_between_attempts():
            return

        ChatVisionMemoryGuardService.release_ocr_memory()

    @classmethod
    def _attempt_uses_easyocr(cls, profile: dict[str, Any] | None) -> bool:
        engines = cls._resolve_region_ocr_engines(profile) or list(
            cls._loop_region_ocr_engines() or ("tesseract",)
        )

        return any(str(engine).strip().lower() == "easyocr" for engine in engines)

    @classmethod
    def _profile_key(cls, profile: dict[str, Any]) -> tuple[Any, ...]:
        engines = profile.get("regionOcrEngines")

        if not isinstance(engines, list) or not engines:
            engines = cls._loop_region_ocr_engines() or ("tesseract",)

        return (
            profile.get("enableRegionOcr"),
            profile.get("regionOcrDpiMultiplier"),
            profile.get("layoutAnalysisEnabled"),
            tuple(str(item).strip().lower() for item in engines if str(item).strip()),
        )

    @classmethod
    def _has_distinct_remaining_profiles(
        cls,
        *,
        history_len: int,
        attempt_slots: list[dict[str, Any]] | None = None,
    ) -> bool:
        attempts = attempt_slots if isinstance(attempt_slots, list) else cls._attempt_profiles()[: cls._max_attempts()]

        if history_len >= len(attempts):
            return False

        seen = {cls._profile_key(profile) for profile in attempts[:history_len]}

        return any(
            cls._profile_key(profile) not in seen
            for profile in attempts[history_len:]
        )

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
    def _pdf_extract_used_embedded_only(cls, pdf_extract: dict[str, Any]) -> bool:
        source = pdf_extract.get("sourceMetadata")

        if not isinstance(source, dict):
            return False

        stages = [str(stage).strip() for stage in (source.get("stages") or []) if str(stage).strip()]

        return "fitz_embedded" in stages and "region_ocr" not in stages

    @classmethod
    def _embedded_text_meets_ocr_gate(cls, pdf_extract: dict[str, Any]) -> bool:
        """Texto embutido ≥ minChars — OCR regional não acrescenta (document_vision.regionOcr)."""
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

        min_chars = ChatDocumentVisionContentService.pdf_region_ocr_min_chars()
        source = pdf_extract.get("sourceMetadata")

        if not isinstance(source, dict):
            return False

        embedded = source.get("embedded")

        if not isinstance(embedded, dict):
            return False

        native_chars = int(embedded.get("nativeCharCount") or 0)
        annotation_chars = int(embedded.get("annotationCharCount") or 0)

        return max(native_chars, annotation_chars, native_chars + annotation_chars) >= min_chars

    @classmethod
    def _embedded_bom_extracted(cls, pdf_extract: dict[str, Any]) -> bool:
        if pdf_extract.get("componentCodes"):
            return True

        scopes = pdf_extract.get("validationScopes")

        if not isinstance(scopes, dict):
            return False

        bom_scope = scopes.get("bom")

        return isinstance(bom_scope, dict) and bool(bom_scope.get("available"))

    @classmethod
    def _try_confirmation_pass(
        cls,
        storage_path: str,
        *,
        filename: str,
        pdf_extract: dict[str, Any],
        confidence: ExtractionConfidenceResult,
        attempt_index: int,
        history: list[ExtractionQualityAttemptResult],
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        from app.domain.services.chat_drawing_tesseract_confirmation_service import (
            ChatDrawingTesseractConfirmationService,
        )

        improved, runs = ChatDrawingTesseractConfirmationService.try_improve(
            storage_path,
            filename=filename,
            pdf_extract=pdf_extract,
            confidence=confidence,
        )

        if not runs:
            return improved, runs

        for run in runs:
            run["afterAttemptId"] = f"attempt_{attempt_index + 1}"
            if history:
                run["afterAttemptIndex"] = history[-1].attempt_index

        return improved, runs

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
        retry_block: dict[str, Any] = {
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
        existing_retry = payload.get("extractionQualityRetry")

        if isinstance(existing_retry, dict) and existing_retry.get("confirmationAttempts"):
            retry_block["confirmationAttempts"] = existing_retry.get("confirmationAttempts")

        payload["extractionQualityRetry"] = retry_block
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
    def _release_memory_between_attempts(cls) -> bool:
        return bool(cls._retry_config().get("releaseMemoryBetweenAttempts", True))

    @classmethod
    def _attempt_profiles(cls) -> list[dict[str, Any]]:
        items = cls._retry_config().get("attempts")

        if isinstance(items, list) and items:
            return [dict(item) for item in items if isinstance(item, dict)]

        return [
            {"id": "standard", "enableRegionOcr": None},
            {"id": "region_ocr", "enableRegionOcr": True},
            {
                "id": "high_dpi_1_5",
                "enableRegionOcr": True,
                "regionOcrDpiMultiplier": 1.5,
            },
            {
                "id": "high_dpi_2_0_layout",
                "enableRegionOcr": True,
                "regionOcrDpiMultiplier": 2.0,
                "layoutAnalysisEnabled": True,
            },
            {
                "id": "easyocr_fusion_2_0",
                "enableRegionOcr": True,
                "regionOcrDpiMultiplier": 2.0,
                "layoutAnalysisEnabled": True,
                "regionOcrEngines": ["tesseract", "easyocr"],
            },
        ]
