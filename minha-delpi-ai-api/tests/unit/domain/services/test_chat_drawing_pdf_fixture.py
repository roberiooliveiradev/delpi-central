from pathlib import Path

from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "drawings"
_TEXT = _FIXTURE_DIR / "sample_carimbo.txt"
_PDF = _FIXTURE_DIR / "sample_carimbo_minimal.pdf"


def _ensure_pdf_fixture() -> Path:
    if _PDF.is_file():
        return _PDF

    import sys

    api_root = Path(__file__).resolve().parents[4]
    root_str = str(api_root)

    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    from scripts.build_drawing_fixture_pdf import build_pdf

    return build_pdf(text_path=_TEXT, output_path=_PDF)


def test_pdf_fixture_extracts_product_code_and_revision():
    pdf_path = _ensure_pdf_fixture()

    parsed = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(pdf_path),
        filename=pdf_path.name,
    )

    assert parsed.get("productCode") == "90260140"
    assert parsed.get("revision") == "01"
    assert parsed.get("legible") is True
    assert "50212194" in (parsed.get("componentCodes") or [])
