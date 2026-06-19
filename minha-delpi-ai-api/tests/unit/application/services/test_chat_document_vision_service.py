import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.infrastructure.config.settings import Settings

_VISION_RUNTIME_STUB = {
    "documentVisionMaxPages": 10,
    "documentVisionStampCropEnabled": False,
    "documentVisionAutoVlmFallback": False,
    "documentVisionImageDescribeEnabled": False,
}


def test_merge_into_drawing_parse_prefers_existing_and_fills_gaps():
    parsed = {
        "productCode": "90260140",
        "revision": None,
        "componentCodes": ["50111111"],
        "legible": False,
        "charCount": 10,
    }
    vision = {
        "revision": "02",
        "componentCodes": ["50122222"],
        "intermediateCodes": ["50133333"],
        "dimensions": {"totalLengthMm": 1000.0},
        "legible": True,
        "charCount": 200,
        "engine": "tesseract",
        "stages": ["native", "tesseract_pdf"],
        "legibilityScore": 0.9,
        "durationMs": 50,
        "schemaVersion": "1.0",
    }

    merged = ChatDocumentVisionService.merge_into_drawing_parse(parsed, vision)

    assert merged["productCode"] == "90260140"
    assert merged["revision"] == "02"
    assert "50111111" in merged["componentCodes"]
    assert "50122222" in merged["componentCodes"]
    assert merged["legible"] is True
    assert merged["extractor"] == "tesseract"
    assert merged["documentVision"]["engine"] == "tesseract"


def test_should_run_for_drawing_when_auto_with_drawing(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

    assert ChatDocumentVisionService.should_run_for_drawing({"drawingAnalysis": True}) is True
    assert ChatDocumentVisionService.should_run_for_drawing({"drawingAnalysis": False}) is False


def test_enrich_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "false")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = False

    base = {"productCode": "90260140", "legible": True}

    assert (
        ChatDocumentVisionService.enrich_drawing_extract(
            base,
            user_id=str(uuid4()),
            session_id=str(uuid4()),
            attachment_ids=[str(uuid4())],
            skills={"drawingAnalysis": True},
        )
        == base
    )


def test_extract_native_from_text(tmp_path):
    pdf_path = tmp_path / "sample.txt"
    pdf_path.write_text("DESENHO 90260140 REV.01\nCOD. CLIENTE ACME", encoding="utf-8")

    with patch.object(
        ChatDocumentVisionService,
        "_stage_native",
        return_value=ChatDocumentVisionService._build_from_text(
            "DESENHO 90260140 REV.01",
            engine="pypdf",
            stages=["native"],
        ),
    ), patch.object(
        ChatDocumentVisionService,
        "_stage_tesseract_pdf",
        return_value={"fullText": "", "warnings": []},
    ), patch(
        "app.application.services.chat_document_vision_service._vision_runtime",
        return_value=_VISION_RUNTIME_STUB,
    ):
        result = ChatDocumentVisionService.extract_from_storage_path(
            str(pdf_path),
            filename="drawing.pdf",
            content_type="application/pdf",
        )

    assert result["productCode"] == "90260140"
    assert result["schemaVersion"] == "1.0"
    assert "native" in result["stages"]


def test_tesseract_pdf_stage_truncates_pages(tmp_path):
    fake_doc = MagicMock()
    fake_doc.page_count = 15
    fake_page = MagicMock()
    fake_pix = MagicMock()
    fake_pix.width = 10
    fake_pix.height = 10
    fake_pix.samples = b"\x00" * 300
    fake_page.get_pixmap.return_value = fake_pix
    fake_doc.load_page.return_value = fake_page

    fake_fitz = MagicMock()
    fake_fitz.open.return_value = fake_doc
    fake_fitz.Matrix = MagicMock()

    with patch.dict("sys.modules", {"fitz": fake_fitz}), patch(
        "pytesseract.image_to_string",
        return_value="90260140 REV.02",
    ), patch(
        "PIL.Image.frombytes",
        return_value=MagicMock(),
    ), patch(
        "app.application.services.chat_document_vision_service._vision_runtime",
        return_value={**_VISION_RUNTIME_STUB, "documentVisionMaxPages": 2},
    ):
        Settings.CHAT_DOCUMENT_VISION_MAX_PAGES = 2
        result = ChatDocumentVisionService._stage_tesseract_pdf(str(tmp_path / "x.pdf"))

    assert "90260140" in result["fullText"]
    assert any("truncated_pages" in item for item in result.get("warnings") or [])


def test_extract_image_uses_tesseract_pipeline(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True

    image_path = tmp_path / "drawing.png"
    image_path.write_bytes(b"png")

    with patch.object(
        ChatDocumentVisionService,
        "_stage_tesseract_image",
        return_value={
            "fullText": "DESENHO 90260140 REV.02",
            "engine": "tesseract",
            "warnings": [],
        },
    ), patch(
        "app.application.services.chat_document_vision_service._vision_runtime",
        return_value=_VISION_RUNTIME_STUB,
    ):
        result = ChatDocumentVisionService.extract_from_storage_path(
            str(image_path),
            filename="drawing.png",
            content_type="image/png",
        )

    assert result["productCode"] == "90260140"
    assert "tesseract_image" in result["stages"]
    assert result["engine"] == "tesseract"


def test_enrich_attachment_excerpt_replaces_placeholder():
    placeholder = (
        "[Imagem scan.png (100×200 PNG). "
        "Conteúdo visual indexado por metadados; descreva o que precisa.]"
    )

    with patch.object(
        ChatDocumentVisionService,
        "extract_from_storage_path",
        return_value={
            "fullText": "PRODUTO 90260140 REV.01",
            "legible": True,
            "charCount": 24,
        },
    ), patch.object(
        ChatDocumentVisionService,
        "should_run_for_attachment",
        return_value=True,
    ):
        text = ChatDocumentVisionService.enrich_attachment_excerpt(
            storage_path="/tmp/scan.png",
            filename="scan.png",
            content_type="image/png",
            extracted_content=placeholder,
        )

    assert "90260140" in text
    assert "Conteúdo visual indexado" not in text


def test_resolve_first_document_attachment_prefers_pdf_then_image():
    pdf = MagicMock()
    pdf.original_filename = "a.pdf"
    pdf.content_type = "application/pdf"
    pdf.storage_path = "/tmp/a.pdf"

    image = MagicMock()
    image.original_filename = "b.png"
    image.content_type = "image/png"
    image.storage_path = "/tmp/b.png"

    with patch.object(
        ChatDocumentVisionService,
        "_list_attachments",
        return_value=[image, pdf],
    ):
        chosen = ChatDocumentVisionService._resolve_first_document_attachment(
            user_id="u",
            session_id="s",
            attachment_ids=["1", "2"],
        )

    assert chosen is pdf

    with patch.object(
        ChatDocumentVisionService,
        "_list_attachments",
        return_value=[image],
    ):
        chosen_image = ChatDocumentVisionService._resolve_first_document_attachment(
            user_id="u",
            session_id="s",
            attachment_ids=["1"],
        )

    assert chosen_image is image


def test_skill_registry_document_vision_with_drawing(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

    from app.domain.skills.chat_skill_registry import ChatSkillRegistry

    flags = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata=None,
        allowed_action_ids=["get_product_analyser"],
        has_agent=True,
    )

    assert flags["drawingAnalysis"] is True
    assert flags["documentVision"] is True


def test_enrich_drawing_extract_uses_delpi_pdf_pipeline(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

    attachment = MagicMock()
    attachment.storage_path = "/tmp/90263489.pdf"
    attachment.original_filename = "90263489.pdf"
    attachment.content_type = "application/pdf"

    drawing_vision = {
        "productCode": "90263489",
        "componentCodes": ["10080627", "10090482", "10091062", "10210754"],
        "intermediateCodes": ["50225215", "50225216", "50225217"],
        "bomRows": [{"code": "10080627"}],
        "bomSource": "bom_region",
        "legible": True,
        "charCount": 2000,
        "extractor": "fitz_embedded",
        "sourceMetadata": {
            "stages": ["fitz_embedded", "region_ocr"],
            "extractor": "fitz_embedded",
        },
        "engine": "fitz_embedded",
        "stages": ["fitz_embedded", "region_ocr"],
        "schemaVersion": "1.0",
        "durationMs": 10.0,
        "legibilityScore": 1.0,
        "bomRowCount": 1,
    }

    with patch.object(
        ChatDocumentVisionService,
        "_resolve_first_document_attachment",
        return_value=attachment,
    ), patch.object(
        ChatDocumentVisionService,
        "_extract_drawing_pdf",
        return_value=drawing_vision,
    ) as drawing_extract, patch.object(
        ChatDocumentVisionService,
        "extract_from_storage_path",
    ) as generic_extract, patch.object(
        ChatDocumentVisionService,
        "persist_attachment_vision_metadata",
    ), patch.object(
        ChatDocumentVisionService,
        "to_document_vision_metadata",
        return_value={},
    ):
        merged = ChatDocumentVisionService.enrich_drawing_extract(
            {"productCode": "90263489"},
            user_id=str(uuid4()),
            session_id=str(uuid4()),
            attachment_ids=[str(uuid4())],
            skills={"drawingAnalysis": True},
        )

    drawing_extract.assert_called_once_with(
        attachment.storage_path,
        filename="90263489.pdf",
    )
    generic_extract.assert_not_called()
    assert "10080627" in merged["componentCodes"]
    assert merged["intermediateCodes"] == ["50225215", "50225216", "50225217"]
    assert merged["documentVision"]["bomRowCount"] == 1
    assert "region_ocr" in (merged.get("documentVision", {}).get("stages") or drawing_vision["stages"])


def test_enrich_drawing_extract_live_90263489_bom_from_region_ocr(monkeypatch):
    from tests.support.drawing_pdf_fixtures import require_drawing_pdf_with_tesseract

    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

    pdf = require_drawing_pdf_with_tesseract("90263489.pdf")
    attachment = MagicMock()
    attachment.storage_path = str(pdf)
    attachment.original_filename = "90263489.pdf"
    attachment.content_type = "application/pdf"

    with patch.object(
        ChatDocumentVisionService,
        "_resolve_first_document_attachment",
        return_value=attachment,
    ), patch.object(
        ChatDocumentVisionService,
        "persist_attachment_vision_metadata",
    ), patch.object(
        ChatDocumentVisionService,
        "to_document_vision_metadata",
        return_value={},
    ):
        merged = ChatDocumentVisionService.enrich_drawing_extract(
            {},
            user_id=str(uuid4()),
            session_id=str(uuid4()),
            attachment_ids=[str(uuid4())],
            skills={"drawingAnalysis": True},
        )

    assert merged.get("productCode") == "90263489"
    assert len(merged.get("componentCodes") or []) >= 4
    assert merged.get("intermediateCodes") == ["50225215", "50225216", "50225217"]
    assert "10081042" not in (merged.get("componentCodes") or [])
    stages = merged.get("documentVision", {}).get("stages") or []
    assert "region_ocr" in stages
