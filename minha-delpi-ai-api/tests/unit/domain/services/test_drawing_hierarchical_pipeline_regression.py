from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.domain.services.chat_drawing_stamp_extraction_service import (
    ChatDrawingStampExtractionService,
)
from tests.fixtures.drawing_hierarchical_regression_cases import synthetic_regression_cases


def test_synthetic_h8_intermediate_code_from_stamp():
    case = next(item for item in synthetic_regression_cases() if item.id == "H8")
    fixture = case.fixture or {}

    extract = ChatDrawingStampExtractionService.extract(
        stamp_text=str(fixture.get("stampText") or ""),
    )

    assert extract.get("productCode") == case.expected_product_code


def test_synthetic_h9_stamp_message_conflict():
    case = next(item for item in synthetic_regression_cases() if item.id == "H9")
    fixture = case.fixture or {}

    extract = ChatDrawingStampExtractionService.extract(
        stamp_text=str(fixture.get("stampText") or ""),
        message_code=str(fixture.get("messageCode") or ""),
    )

    assert extract.get("productCode") == str(fixture.get("messageCode"))
    assert any(item.get("type") == "stamp_vs_message" for item in extract.get("conflicts") or [])


def test_synthetic_h10_unresolved_stamp():
    case = next(item for item in synthetic_regression_cases() if item.id == "H10")
    fixture = case.fixture or {}

    extract = ChatDrawingStampExtractionService.extract(
        stamp_text=str(fixture.get("stampText") or ""),
    )

    assert extract.get("productCode") is None
    assert extract.get("productCodeSource") == "unresolved"


def test_synthetic_h8_through_build_from_text():
    case = next(item for item in synthetic_regression_cases() if item.id == "H8")
    fixture = case.fixture or {}

    result = ChatDocumentVisionService._build_from_text(
        "ruido global",
        engine="tesseract",
        stages=["tesseract"],
        source_metadata={
            "stampText": str(fixture.get("stampText") or ""),
            "filename": "50232222.pdf",
        },
    )

    assert result.get("productCode") == case.expected_product_code
