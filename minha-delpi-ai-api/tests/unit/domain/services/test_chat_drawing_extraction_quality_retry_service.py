"""Retentativas de extração até confiança ≥ 95%."""

from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
    ExtractionConfidenceResult,
)
from app.domain.services.chat_drawing_extraction_quality_retry_service import (
    ChatDrawingExtractionQualityRetryService,
)


def test_retry_stops_on_first_attempt_when_confident(monkeypatch):
    attempts = []

    def fake_extract(storage_path, *, filename="", attempt=None):
        attempts.append(attempt)
        return {
            "productCode": "90264227",
            "legible": True,
            "componentCodes": ["10081867", "50215425"],
            "intermediateCodes": ["50215425"],
            "validationScopes": {"bom": {"available": True}},
            "dimensions": {
                "leftDecapeMm": 4.0,
                "segmentLengthsMm": [140.0],
            },
            "titleBlock": {"productCode": "90264227"},
            "sourceMetadata": {"stages": ["region_ocr"]},
        }

    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_extract_once",
        staticmethod(fake_extract),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionConfidenceService,
        "evaluate_for_extraction",
        classmethod(
            lambda cls, *, pdf_extract: ExtractionConfidenceResult(
                score=0.96,
                threshold=0.95,
                meets_threshold=True,
                components={"all": 0.96},
                reasons=(),
            )
        ),
    )

    result = ChatDrawingExtractionQualityRetryService.extract_until_confident(
        "/tmp/x.pdf",
        filename="x.pdf",
    )

    retry = result.get("extractionQualityRetry") or {}

    assert retry.get("stoppedReason") == "target_reached"
    assert retry.get("attemptCount") == 1
    assert len(attempts) == 1


def test_retry_runs_multiple_attempts_until_max(monkeypatch):
    scores = [0.5, 0.7, 0.82, 0.88, 0.91]
    call = {"index": 0}

    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_max_attempts",
        classmethod(lambda cls: 5),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_attempt_profiles",
        classmethod(
            lambda cls: [
                {"id": f"attempt_{index}"} for index in range(5)
            ]
        ),
    )

    def fake_extract_improving(storage_path, *, filename="", attempt=None):
        idx = min(call["index"], 4)
        return {
            "productCode": "90264227",
            "componentCodes": ["10081867"] * (idx + 1),
            "sourceMetadata": {"stages": ["region_ocr"] if idx > 1 else []},
        }

    def rolling_confidence(cls, *, pdf_extract):
        score = scores[min(call["index"], len(scores) - 1)]
        call["index"] += 1

        return ExtractionConfidenceResult(
            score=score,
            threshold=0.95,
            meets_threshold=score >= 0.95,
            components={"score": score},
            reasons=(),
        )

    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_extract_once",
        staticmethod(fake_extract_improving),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_release_extraction_memory",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionConfidenceService,
        "evaluate_for_extraction",
        classmethod(rolling_confidence),
    )

    result = ChatDrawingExtractionQualityRetryService.extract_until_confident(
        "/tmp/x.pdf",
        filename="90264227-1.pdf",
    )
    retry = result.get("extractionQualityRetry") or {}

    assert retry.get("stoppedReason") == "max_attempts"
    assert retry.get("attemptCount") == 5
    assert retry.get("selectedScorePercent") == 91


def test_retry_releases_memory_between_attempts(monkeypatch):
    released = {"count": 0}

    def fake_release(cls) -> None:
        released["count"] += 1

    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_max_attempts",
        classmethod(lambda cls: 2),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_attempt_profiles",
        classmethod(
            lambda cls: [
                {"id": "standard"},
                {"id": "high_dpi_tesseract"},
            ]
        ),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_release_extraction_memory",
        classmethod(fake_release),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_extract_once",
        staticmethod(
            lambda storage_path, *, filename="", attempt=None: {
                "productCode": "90264227",
                "componentCodes": ["10081867"],
            }
        ),
    )

    scores = iter([0.6, 0.72])

    def rolling_confidence(cls, *, pdf_extract):
        return ExtractionConfidenceResult(
            score=next(scores),
            threshold=0.95,
            meets_threshold=False,
            components={},
            reasons=(),
        )

    monkeypatch.setattr(
        ChatDrawingExtractionConfidenceService,
        "evaluate_for_extraction",
        classmethod(rolling_confidence),
    )

    ChatDrawingExtractionQualityRetryService.extract_until_confident(
        "/tmp/x.pdf",
        filename="x.pdf",
    )

    assert released["count"] == 1


def test_retry_stops_after_two_attempts_without_improvement(monkeypatch):
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_max_attempts",
        classmethod(lambda cls: 2),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_attempt_profiles",
        classmethod(
            lambda cls: [
                {"id": "standard"},
                {"id": "high_dpi_tesseract"},
            ]
        ),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_release_extraction_memory",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_extract_once",
        staticmethod(
            lambda storage_path, *, filename="", attempt=None: {
                "productCode": "90264227",
                "componentCodes": ["10081867"],
            }
        ),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionConfidenceService,
        "evaluate_for_extraction",
        classmethod(
            lambda cls, *, pdf_extract: ExtractionConfidenceResult(
                score=0.55,
                threshold=0.95,
                meets_threshold=False,
                components={},
                reasons=(),
            )
        ),
    )

    result = ChatDrawingExtractionQualityRetryService.extract_until_confident(
        "/tmp/x.pdf",
        filename="x.pdf",
    )
    retry = result.get("extractionQualityRetry") or {}

    assert retry.get("attemptCount") == 2
    assert retry.get("stoppedReason") == "no_improvement"


def test_retry_loop_defaults_to_tesseract_only(monkeypatch):
    assert ChatDrawingExtractionQualityRetryService._resolve_region_ocr_engines(
        {"id": "standard"}
    ) == ["tesseract"]

    engines_seen: list[tuple[str, ...] | None] = []

    def fake_single_pass(storage_path, *, filename="", extraction_options=None):
        from app.domain.services.chat_pdf_region_ocr_engine_service import (
            ChatPdfRegionOcrEngineService,
        )

        engines_seen.append(ChatPdfRegionOcrEngineService._runtime_engines_override)
        return {
            "productCode": "90264227",
            "legible": True,
            "componentCodes": ["10081867"],
            "sourceMetadata": {"stages": ["region_ocr"]},
        }

    monkeypatch.setattr(
        "app.domain.services.chat_drawing_pdf_extraction_service.ChatDrawingPdfExtractionService._extract_single_pass",
        staticmethod(fake_single_pass),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_max_attempts",
        classmethod(lambda cls: 1),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_release_extraction_memory",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionConfidenceService,
        "evaluate_for_extraction",
        classmethod(
            lambda cls, *, pdf_extract: ExtractionConfidenceResult(
                score=0.96,
                threshold=0.95,
                meets_threshold=True,
                components={},
                reasons=(),
            )
        ),
    )

    result = ChatDrawingExtractionQualityRetryService.extract_until_confident(
        "/tmp/x.pdf",
        filename="x.pdf",
    )

    assert engines_seen == [("tesseract",)]
    assert result["extractionQualityRetry"]["regionOcrEngines"] == ["tesseract"]
