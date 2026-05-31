from pathlib import Path

from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)

_FIXTURE = (
    Path(__file__).resolve().parents[3] / "fixtures" / "drawings" / "sample_carimbo.txt"
)


def test_fixture_sample_carimbo_parses():
    text = _FIXTURE.read_text(encoding="utf-8")
    parsed = ChatDrawingPdfExtractionService.parse_from_text(text)

    assert parsed["productCode"] == "90260140"
    assert parsed["revision"] == "01"
    assert "50212194" in parsed["componentCodes"]
    assert parsed["dimensions"]["totalLengthMm"] == 1400.0
