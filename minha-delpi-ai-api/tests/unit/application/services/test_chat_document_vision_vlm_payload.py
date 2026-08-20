"""Payload VLM regional, prompts drawing e parse CARIMBO/BOM/PAGINA."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.chat_document_vision.chat_document_vision_stage_service import (
    ChatDocumentVisionStageService,
)
from app.application.services.chat_document_vision.chat_document_vision_vlm_payload_service import (
    ChatDocumentVisionVlmPayloadService,
)
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from tests.support.drawing_pdf_fixtures import require_drawing_pdf


def test_vlm_drawing_settings_and_prompt_from_bundle():
    assert ChatDocumentVisionContentService.vlm_max_images() >= 1
    assert ChatDocumentVisionContentService.vlm_drawing_regions()[:2] == ("stamp", "bom")
    assert ChatDocumentVisionContentService.vlm_include_overview() is True

    prompt = ChatDocumentVisionContentService.vlm_drawing_ocr_prompt()
    assert "CARIMBO:" in prompt
    assert "BOM:" in prompt
    assert "PAGINA:" in prompt

    hinted = ChatDocumentVisionContentService.vlm_drawing_ocr_prompt(
        partial_ocr="STAMP:\nCODIGO 90261842 REV A"
    )
    assert "Dica do OCR parcial" in hinted
    assert "90261842" in hinted


def test_parse_drawing_vlm_response_sections():
    content = """
CARIMBO:
PRODUTO 90261842
REV 01

BOM:
1 90260141 2 PC TERMINAL

PAGINA:
vista geral do chicote
"""
    sections = ChatDocumentVisionStageService.parse_drawing_vlm_response(content)

    assert "90261842" in sections.get("stamp", "")
    assert "90260141" in sections.get("bom", "")
    assert "chicote" in sections.get("page", "").lower()


def test_parse_drawing_vlm_response_without_sections_returns_empty():
    sections = ChatDocumentVisionStageService.parse_drawing_vlm_response(
        "texto livre sem marcadores"
    )

    assert sections == {}


def test_vlm_payload_full_page_without_drawing_flag(tmp_path):
    png = tmp_path / "page.png"
    from PIL import Image

    Image.new("RGB", (32, 32), color=(255, 255, 255)).save(png)

    payload = ChatDocumentVisionVlmPayloadService.build(
        str(png),
        filename="page.png",
        content_type="image/png",
        use_drawing_regions=False,
        purpose="ocr",
        is_image=True,
    )

    assert payload["promptContext"]["mode"] == "full_page"
    assert len(payload["imagesB64"]) == 1
    assert payload["vlmRegionsSent"] == ["page"]
    assert "carimbo" not in payload["prompt"].lower() or "Extraia todo" in payload["prompt"]


def test_vlm_payload_drawing_regions_order_and_caps():
    pdf_path = require_drawing_pdf("90261842.pdf")

    fake_image = MagicMock()
    with patch(
        "app.domain.services.chat_drawing_region_service.ChatDrawingRegionService.render_region_image",
        return_value=fake_image,
    ):
        with patch(
            "app.domain.services.chat_drawing_region_service.ChatDrawingRegionService.resolve_region_bboxes_for_page",
            return_value=(
                {
                    "stamp": [0.5, 0.62, 1.0, 1.0],
                    "bom": [0.0, 0.0, 0.55, 0.35],
                },
                {},
            ),
        ):
            with patch(
                "app.application.services.chat_document_vision.chat_document_vision_facade_access.vision_service"
            ) as vision_svc:
                vision_svc.return_value._pil_to_base64_png.side_effect = (
                    lambda _img: "YmFzZTY0"
                )
                payload = ChatDocumentVisionVlmPayloadService.build(
                    str(pdf_path),
                    filename="90261842.pdf",
                    content_type="application/pdf",
                    use_drawing_regions=True,
                    purpose="ocr",
                    partial_ocr_texts={"stamp": "CODIGO 90261842"},
                )

    assert payload["promptContext"]["mode"] == "drawing_regions"
    assert payload["vlmRegionsSent"][0] == "stamp"
    assert "bom" in payload["vlmRegionsSent"]
    assert payload["vlmImageCount"] == len(payload["imagesB64"])
    assert payload["vlmImageCount"] <= ChatDocumentVisionContentService.vlm_max_images()
    assert "CARIMBO:" in payload["prompt"]
    assert "90261842" in payload["prompt"]


def test_payload_suggests_drawing_regions_from_region_ocr_flag():
    assert ChatDocumentVisionStageService._payload_suggests_drawing_regions(
        {"regionOcrAttempted": True},
        stages=[],
    )
    assert not ChatDocumentVisionStageService._payload_suggests_drawing_regions(
        {"regionTexts": {}},
        stages=["tesseract_pdf"],
    )
    assert ChatDocumentVisionStageService._payload_suggests_drawing_regions(
        {},
        stages=["tesseract_region_ocr"],
    )


def test_stage_ollama_vlm_drawing_wires_payload_and_parse(monkeypatch):
    from app.application.services.chat_document_vision_service import ChatDocumentVisionService

    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")

    fake_payload = {
        "imagesB64": ["a", "b"],
        "regionLabels": ["stamp", "bom"],
        "vlmRegionsSent": ["stamp", "bom"],
        "vlmImageCount": 2,
        "prompt": "CARIMBO:\n...\nBOM:\n...",
        "promptContext": {"mode": "drawing_regions"},
        "warnings": [],
    }

    gateway = MagicMock()
    gateway.describe.return_value = (
        "CARIMBO:\n90261842 REV 01\nBOM:\n1 90260141 2 PC\nPAGINA:\noverview"
    )
    gateway.provider_name.return_value = "openai_compatible"

    with patch(
        "app.application.services.chat_document_vision.chat_document_vision_vlm_payload_service.ChatDocumentVisionVlmPayloadService.build",
        return_value=fake_payload,
    ):
        with patch(
            "app.composition.vision_llm_composer.make_vision_llm_gateway",
            return_value=gateway,
        ):
            result = ChatDocumentVisionService._stage_ollama_vlm(
                "/tmp/drawing.pdf",
                filename="90261842.pdf",
                content_type="application/pdf",
                purpose="ocr",
                use_drawing_regions=True,
            )

    assert gateway.describe.call_count == 1
    call_kwargs = gateway.describe.call_args.kwargs
    assert call_kwargs["images_b64"] == ["a", "b"]
    assert "CARIMBO" in call_kwargs["prompt"]
    assert result.get("vlmRegionsSent") == ["stamp", "bom"]
    assert "90261842" in str(result.get("stampText") or result.get("fullText") or "")
