from app.domain.services.chat_drawing_bom_row_sanitization_service import (
    ChatDrawingBomRowSanitizationService,
)
from app.domain.services.chat_pdf_region_ocr_fusion_service import (
    ChatPdfRegionOcrFusionService,
)


def test_fuse_prefers_line_with_more_component_codes():
    tesseract = "10081867 | TERM\n90264297 | CHICOTE TRR"
    easyocr = "10081867 | TERM\n10091640 | CONECTOR"

    fused = ChatPdfRegionOcrFusionService.fuse([tesseract, easyocr])

    assert "10091640" in fused
    assert "10081867" in fused


def test_product_ghost_row_is_removed():
    rows = [
        {"code": "90264297", "description": "CHICOTE TRR-ITCC-0039"},
        {"code": "10081867", "description": "TERM"},
    ]

    sanitized = ChatDrawingBomRowSanitizationService.sanitize_rows(
        rows,
        product_code="90264227",
    )

    assert len(sanitized) == 1
    assert sanitized[0]["code"] == "10081867"


def test_nested_component_codes_from_row_description():
    rows = [
        {
            "code": "50215425",
            "description": "CA22 | 10440133 CABO TEF",
        }
    ]

    codes = ChatDrawingBomRowSanitizationService.nested_component_codes(rows)

    assert codes == ["10440133"]


def test_dedupe_keeps_distinct_codes_without_catalog_reconcile():
    codes = ChatDrawingBomRowSanitizationService.dedupe_component_codes(
        ["10091640", "40091640"],
    )

    assert codes == ["10091640", "40091640"]
