"""Confirmação focal — plano diagnóstico e re-OCR Tesseract."""

from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
    ExtractionConfidenceResult,
)
from app.domain.services.chat_drawing_extraction_diagnostic_service import (
    ChatDrawingExtractionDiagnosticService,
)
from app.domain.services.chat_drawing_extraction_quality_retry_service import (
    ChatDrawingExtractionQualityRetryService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService
from app.domain.services.chat_drawing_tesseract_confirmation_service import (
    ChatDrawingTesseractConfirmationService,
)


def test_diagnostic_plan_maps_weak_stamp_to_stamp_regions():
    confidence = ExtractionConfidenceResult(
        score=0.72,
        threshold=0.95,
        meets_threshold=False,
        components={
            "stamp": 0.75,
            "bom_scope": 0.96,
            "legibility": 0.96,
        },
        reasons=("product_code_without_title_block",),
    )

    plan = ChatDrawingExtractionDiagnosticService.build_plan(confidence)

    assert plan is not None
    assert "stamp" in plan.regions
    assert "title" in plan.regions
    assert "bom" not in plan.regions


def test_diagnostic_returns_none_when_threshold_met():
    confidence = ExtractionConfidenceResult(
        score=0.96,
        threshold=0.95,
        meets_threshold=True,
        components={"stamp": 0.96},
        reasons=(),
    )

    assert ChatDrawingExtractionDiagnosticService.build_plan(confidence) is None


def test_try_improve_merges_confirmed_regions(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_ocr(storage_path, regions, *, dpi_multiplier=1.5, engines=None):
        calls.append(tuple(regions))
        return {"stamp": "CODIGO DELPI 90264227 REV 01"}, {"stamp": {"engine": "tesseract"}}

    monkeypatch.setattr(
        ChatDrawingRegionService,
        "ocr_selected_drawing_regions",
        staticmethod(fake_ocr),
    )

    base = {
        "productCode": None,
        "componentCodes": [],
        "sourceMetadata": {"regionTexts": {}, "stages": ["fitz_embedded"]},
    }
    confidence = ExtractionConfidenceResult(
        score=0.55,
        threshold=0.95,
        meets_threshold=False,
        components={"stamp": 0.4, "bom_scope": 0.5},
        reasons=("product_code_missing",),
    )

    def fake_parse(full_text, *, metadata=None, storage_path=""):
        return {
            "productCode": "90264227",
            "revision": "01",
            "componentCodes": [],
            "titleBlock": {"productCode": "90264227"},
            "validationScopes": {"bom": {"available": False}},
            "dimensions": {},
            "legible": True,
            "sourceMetadata": metadata or {},
        }

    monkeypatch.setattr(
        ChatDrawingPdfExtractionService,
        "parse_from_text",
        staticmethod(fake_parse),
    )

    monkeypatch.setattr(
        ChatDrawingExtractionConfidenceService,
        "evaluate_for_extraction",
        classmethod(
            lambda cls, *, pdf_extract: ExtractionConfidenceResult(
                score=0.97,
                threshold=0.95,
                meets_threshold=True,
                components={"stamp": 0.97},
                reasons=(),
            )
        ),
    )

    improved, runs = ChatDrawingTesseractConfirmationService.try_improve(
        "/tmp/x.pdf",
        filename="x.pdf",
        pdf_extract=base,
        confidence=confidence,
    )

    assert improved is not None
    assert improved.get("productCode") == "90264227"
    assert runs
    assert runs[0]["improved"] is True
    assert "stamp" in calls[0]


def test_retry_stops_on_confirmation_reached(monkeypatch):
    attempts = []

    def fake_extract(storage_path, *, filename="", attempt=None):
        attempts.append(attempt)
        return {
            "productCode": None,
            "legible": False,
            "componentCodes": [],
            "validationScopes": {},
            "dimensions": {},
            "sourceMetadata": {"stages": ["fitz_embedded"]},
        }

    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_extract_once",
        staticmethod(fake_extract),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_max_attempts",
        classmethod(lambda cls: 3),
    )
    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_attempt_profiles",
        classmethod(
            lambda cls: [
                {"id": "standard"},
                {"id": "region_ocr", "enableRegionOcr": True},
                {"id": "high_dpi", "enableRegionOcr": True, "regionOcrDpiMultiplier": 1.5},
            ]
        ),
    )

    scores_iter = iter([0.6, 0.97, 0.97])

    def evaluate(cls, *, pdf_extract):
        score = next(scores_iter)
        return ExtractionConfidenceResult(
            score=score,
            threshold=0.95,
            meets_threshold=score >= 0.95,
            components={"stamp": score},
            reasons=("product_code_missing",) if score < 0.95 else (),
        )

    monkeypatch.setattr(
        ChatDrawingExtractionConfidenceService,
        "evaluate_for_extraction",
        classmethod(evaluate),
    )

    monkeypatch.setattr(
        ChatDrawingExtractionQualityRetryService,
        "_try_confirmation_pass",
        classmethod(
            lambda cls, storage_path, *, filename, pdf_extract, confidence, attempt_index, history: (
                {
                    **pdf_extract,
                    "productCode": "90264227",
                    "titleBlock": {"productCode": "90264227"},
                    "legible": True,
                },
                [{"passIndex": 0, "improved": True}],
            )
        ),
    )

    result = ChatDrawingExtractionQualityRetryService.extract_until_confident(
        "/tmp/x.pdf",
        filename="x.pdf",
    )

    retry = result.get("extractionQualityRetry") or {}

    assert retry.get("stoppedReason") == "confirmation_reached"
    assert len(attempts) == 1
