from app.domain.services.chat_pdf_region_ocr_fusion_service import (
    ChatPdfRegionOcrFusionService,
)


def test_fuse_prefers_line_with_more_component_codes():
    tesseract = "10081867 | TERM\n90264297 | CHICOTE TRR"
    easyocr = "10081867 | TERM\n10091640 | CONECTOR"

    fused = ChatPdfRegionOcrFusionService.fuse([tesseract, easyocr])

    assert "10091640" in fused
    assert "10081867" in fused


def test_fuse_bom_merges_unique_lines_with_engine_weight():
    by_engine = {
        "tesseract": "10081867 | TERM\n50215426 | CT26",
        "easyocr": "10081867 | TERM\n10091640 | CONECTOR",
    }

    fused = ChatPdfRegionOcrFusionService.fuse_bom(by_engine)

    assert "10091640" in fused
    assert "50215426" in fused


def test_fuse_bom_votes_digits_by_engine_confidence_not_catalog():
    by_engine = {
        "tesseract": "50215426 | 10440154",
        "easyocr": "50215426 | 10440134",
    }
    tokens = {
        "tesseract": [
            {"code": "10440154", "confidence": 0.55, "lineIndex": 0, "codeIndex": 1},
        ],
        "easyocr": [
            {"code": "10440134", "confidence": 0.92, "lineIndex": 0, "codeIndex": 1},
        ],
    }

    fused = ChatPdfRegionOcrFusionService.fuse_bom(
        by_engine,
        code_tokens_by_engine=tokens,
    )

    assert "10440134" in fused
    assert "10440154" not in fused


def test_fuse_bom_keeps_agreed_digits_when_engines_match():
    by_engine = {
        "tesseract": "50215425 | 10440133",
        "easyocr": "50215425 | 10440133",
    }

    fused = ChatPdfRegionOcrFusionService.fuse_bom(by_engine)

    assert "10440133" in fused
