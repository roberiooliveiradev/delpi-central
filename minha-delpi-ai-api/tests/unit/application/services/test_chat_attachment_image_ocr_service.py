from pathlib import Path
from unittest.mock import patch

from app.application.services.chat_attachment_image_ocr_service import (
    ChatAttachmentImageOcrService,
)
from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.application.services.chat_attachment_text_extractor import (
    ChatAttachmentTextExtractor,
)


def test_ocr_disabled_skips_extraction(tmp_path: Path):
    png = tmp_path / "foto.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    with patch.object(ChatAttachmentImageOcrService, "is_enabled", return_value=False):
        result = ChatAttachmentTextExtractor().extract(
            storage_path=str(png),
            filename="foto.png",
            content_type="image/png",
        )

    assert result["metadata"]["extractor"] == "image_metadata"
    assert result["metadata"]["ocr"]["used"] is False


def test_ocr_with_text_uses_image_ocr_extractor(tmp_path: Path):
    png = tmp_path / "etiqueta.png"
    png.write_bytes(b"not-a-real-png")

    with patch.object(ChatAttachmentImageOcrService, "is_enabled", return_value=True):
        with patch.object(
            ChatAttachmentImageOcrService,
            "try_extract_text",
            return_value={
                "text": "Produto ABC 123",
                "used": True,
                "reason": None,
                "charCount": 15,
            },
        ):
            result = ChatAttachmentTextExtractor().extract(
                storage_path=str(png),
                filename="etiqueta.png",
                content_type="image/png",
            )

    assert result["metadata"]["extractor"] == "image_ocr"
    assert "Produto ABC 123" in result["content"]

    preview = ChatAttachmentPreviewService.build_from_extracted(
        result,
        filename="etiqueta.png",
    )

    assert preview.get("ocr") is True
    assert preview.get("ocrCharCount") == 15
