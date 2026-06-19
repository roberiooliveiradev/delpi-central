from unittest.mock import patch

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.infrastructure.config.settings import Settings
from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService
from tests.fixtures.document_vision_regression_cases import REGRESSION_CASES


def test_build_from_text_prefers_bom_and_dimensions_regions():
    result = ChatDocumentVisionService._build_from_text(
        "90299999 LISTA DE MATERIAIS 90288888",
        engine="tesseract",
        stages=["tesseract"],
        source_metadata={
            "stampText": "CODIGO DELPI 90261040",
            "bomText": "01 10400006 2 TERMINAL\n02 90260141 1 CABO",
            "dimensionsText": "COMPR TOTAL 1200 mm\nDECAPE ESQUERDO 15",
            "filename": "90261040.pdf",
        },
    )

    bom_codes = [row["code"] for row in result.get("bomRows") or []]

    assert result.get("productCode") == "90261040"
    assert "10400006" in bom_codes
    assert result.get("dimensions", {}).get("totalLengthMm") == 1200.0
    assert "bom_region" in (result.get("stages") or [])
    assert "dimensions_ocr" in (result.get("stages") or [])


def test_regression_v6_bom_heuristic():
    case = next(item for item in REGRESSION_CASES if item["id"] == "V6")
    rows = ChatDocumentVisionBomService.extract_bom_rows(case["bom_text"])

    assert [row["code"] for row in rows] == case["expect_bom_codes"]


def test_regression_v9_title_block_on_tesseract_stamp(monkeypatch):
    case = next(item for item in REGRESSION_CASES if item["id"] == "V9")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_BACKEND", "tesseract")
    Settings.CHAT_DOCUMENT_VISION_BACKEND = "tesseract"

    with patch.object(
        ChatDocumentVisionService,
        "_stage_tesseract_pdf",
        return_value={
            "fullText": case["ocr_text"],
            "engine": "tesseract",
            "pageCount": 1,
            "stampCrop": True,
            "stampText": case.get("stamp_text", ""),
            "warnings": [],
        },
    ):
        with patch.object(
            ChatDocumentVisionService,
            "_stage_native",
            return_value={"fullText": "", "legible": False},
        ):
            result = ChatDocumentVisionService.extract_from_storage_path(
                "/tmp/drawing.pdf",
                filename="drawing.pdf",
                content_type="application/pdf",
            )

    title_block = result.get("titleBlock")

    assert isinstance(title_block, dict)
    assert title_block.get("fields", {}).get("code") == case["expect_product_code"]


def test_regression_v8_merge_product_code():
    case = next(item for item in REGRESSION_CASES if item["id"] == "V8")

    merged = ChatDocumentVisionService.merge_into_drawing_parse(
        {"productCode": case.get("drawing_product_code")},
        {
            "productCode": case["vision_product_code"],
            "engine": case["vision_engine"],
            "stages": ["tesseract"],
            "charCount": 100,
            "legible": True,
        },
    )

    assert merged["productCode"] == case["expect_merged_code"]
    assert merged["documentVision"]["engine"] == "tesseract"


def test_extract_adds_stamp_crop_stage(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_BACKEND", "tesseract")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_BACKEND = "tesseract"

    with patch.object(
        ChatDocumentVisionService,
        "_stage_native",
        return_value={"fullText": "", "legible": False},
    ):
        with patch.object(
            ChatDocumentVisionService,
            "_stage_tesseract_pdf",
            return_value={
                "fullText": "TEXTO OCR",
                "stampCrop": True,
                "warnings": ["stamp_crop_applied"],
            },
        ):
            result = ChatDocumentVisionService.extract_from_storage_path(
                "/tmp/drawing.pdf",
                filename="drawing.pdf",
            )

    assert "tesseract_stamp_crop" in (result.get("stages") or [])
