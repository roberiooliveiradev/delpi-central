"""Onda B — confirmação BOM ancorada no payload `/analyser`."""

from app.application.services.chat_drawing_analyser_bom_confirmation_orchestration_service import (
    ChatDrawingAnalyserBomConfirmationOrchestrationService,
)
from app.domain.services.chat_drawing_analyser_anchor_service import (
    ChatDrawingAnalyserAnchorService,
)
from app.domain.services.chat_drawing_bom_anchor_confirmation_service import (
    ChatDrawingBomAnchorConfirmationService,
)
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ExtractionConfidenceResult,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService


def _analyser_root_fixture() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50230969",
                    "description": "PI PAI",
                    "type": "PI",
                    "components": [
                        {
                            "code": "50212870",
                            "description": "PI FILHO 70",
                            "type": "PI",
                            "components": [],
                        },
                        {
                            "code": "50212871",
                            "description": "PI FILHO 71",
                            "type": "PI",
                            "components": [],
                        },
                    ],
                },
                {
                    "code": "10081867",
                    "description": "MP",
                    "type": "MP",
                    "components": [],
                },
            ]
        }
    }


def test_should_anchor_when_bom_scope_weak():
    confidence = ExtractionConfidenceResult(
        score=0.88,
        threshold=0.95,
        meets_threshold=False,
        components={"bom_scope": 0.8, "stamp": 0.98},
        reasons=("bom_scope_partial",),
    )

    assert ChatDrawingAnalyserAnchorService.should_anchor_bom(
        pdf_extract={"productCode": "90264227"},
        confidence=confidence,
    )


def test_should_not_anchor_when_bom_components_strong():
    confidence = ExtractionConfidenceResult(
        score=0.97,
        threshold=0.95,
        meets_threshold=True,
        components={"bom_scope": 0.97, "bom_completeness": 0.98},
        reasons=(),
    )

    assert not ChatDrawingAnalyserAnchorService.should_anchor_bom(
        pdf_extract={"productCode": "90264227"},
        confidence=confidence,
    )


def test_build_anchor_collects_structure_codes():
    root = _analyser_root_fixture()

    anchor = ChatDrawingAnalyserAnchorService.build_anchor(
        analyser_root=root,
        product_code="90262834",
    )

    assert anchor is not None
    assert "50212870" in anchor.expected_codes
    assert "10081867" in anchor.expected_codes


def test_anchor_confirmation_injects_missing_codes(monkeypatch):
    monkeypatch.setattr(
        ChatDrawingRegionService,
        "ocr_selected_drawing_regions",
        staticmethod(
            lambda storage_path, regions, *, dpi_multiplier=1.5, engines=None: (
                {"bom": "50212870 50212871"},
                {"bom": {"engine": "tesseract"}},
            )
        ),
    )

    base = {
        "productCode": "90262834",
        "componentCodes": ["50212870"],
        "sourceMetadata": {
            "regionTexts": {"bom": "50212870"},
            "stages": ["fitz_embedded"],
        },
    }
    confidence = ExtractionConfidenceResult(
        score=0.7,
        threshold=0.95,
        meets_threshold=False,
        components={"bom_scope": 0.6, "bom_completeness": 0.5},
        reasons=("component_codes_missing",),
    )

    def fake_parse(full_text, *, metadata=None, storage_path=""):
        return {
            **base,
            "componentCodes": ["50212870"],
            "sourceMetadata": metadata or {},
        }

    monkeypatch.setattr(
        ChatDrawingPdfExtractionService,
        "parse_from_text",
        staticmethod(fake_parse),
    )

    anchor = ChatDrawingAnalyserAnchorService.build_anchor(
        analyser_root=_analyser_root_fixture(),
        product_code="90262834",
    )

    improved, run_meta = ChatDrawingBomAnchorConfirmationService.try_improve_with_anchor(
        "/tmp/x.pdf",
        filename="x.pdf",
        pdf_extract=base,
        anchor=anchor,
        confidence=confidence,
    )

    assert improved is not None
    assert "50212871" in (improved.get("componentCodes") or [])
    assert run_meta.get("addedCodes") == ["50212871"]


def test_orchestration_applies_anchor_after_code_resolution(monkeypatch):
    pdf_extract = {
        "productCode": None,
        "componentCodes": [],
        "sourceMetadata": {
            "storagePath": "/tmp/x.pdf",
            "regionTexts": {"bom": "50123456"},
            "stages": ["fitz_embedded"],
        },
    }

    monkeypatch.setattr(
        ChatDrawingAnalyserAnchorService,
        "should_anchor_bom",
        classmethod(lambda cls, **kwargs: True),
    )
    monkeypatch.setattr(
        "app.application.services.chat_drawing_analyser_bom_confirmation_orchestration_service.ChatDrawingAnalyserFetchService.fetch_root",
        classmethod(lambda cls, **kwargs: _analyser_root_fixture()),
    )
    monkeypatch.setattr(
        ChatDrawingBomAnchorConfirmationService,
        "try_improve_with_anchor",
        classmethod(
            lambda cls, storage_path, *, filename, pdf_extract, anchor, confidence=None: (
                {
                    **pdf_extract,
                    "componentCodes": ["50212870"],
                    "bomAnchorConfirmation": {"addedCodes": ["50212870"]},
                },
                {"phase": "analyser_bom_anchor", "improved": True},
            )
        ),
    )

    result = ChatDrawingAnalyserBomConfirmationOrchestrationService.try_anchor_after_code_resolution(
        pdf_extract=pdf_extract,
        product_code="90264227",
        access_token="token",
        storage_path="/tmp/x.pdf",
        filename="x.pdf",
    )

    retry = result.get("extractionQualityRetry") or {}

    assert "50212870" in (result.get("componentCodes") or [])
    assert retry.get("analyserBomAnchor", {}).get("applied") is True
    assert retry.get("confirmationAttempts")
