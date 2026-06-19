"""Regressão live — desenho 90264227-1.pdf (FLEXTRONICS chicote)."""

from tests.support.drawing_pdf_fixtures import require_drawing_pdf_with_tesseract

from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from tests.unit.domain.services.test_chat_drawing_bom_comparison_service import (
    _payload_90264227,
)


def test_live_extraction_90264227_1_pdf():
    pdf = require_drawing_pdf_with_tesseract("90264227-1.pdf")

    parsed = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(pdf),
        filename="90264227-1.pdf",
    )

    assert parsed.get("productCode") == "90264227"
    assert "90264297" not in (parsed.get("componentCodes") or [])
    assert "10081867" in parsed["componentCodes"]
    assert "10091640" in parsed["componentCodes"]
    assert "10440133" in parsed["componentCodes"]
    assert "10440134" in parsed["componentCodes"]
    assert parsed.get("intermediateCodes") == ["50215425", "50215426", "50215433"]

    cmp = ChatDrawingBomComparisonService.compare(
        root=_payload_90264227(),
        pdf_extract=parsed,
        product_code="90264227",
    )

    assert "90264297" not in cmp.extra_in_pdf
    assert "50215434" in cmp.missing_in_pdf
    assert "10440133" not in cmp.extra_in_pdf
    assert "10440134" not in cmp.extra_in_pdf

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264227(),
        pdf_extract=parsed,
        product_code="90264227",
    )

    assert not any(
        item.get("item") == "Componente extra no PDF"
        for item in items
    )
