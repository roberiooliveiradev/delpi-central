import tempfile
from pathlib import Path

from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.application.services.chat_attachment_text_extractor import (
    ChatAttachmentTextExtractor,
)


def _minimal_png(path: Path) -> None:
    # PNG 1x1 transparent pixel
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    path.write_bytes(png)


def test_extract_image_supported():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "grafico.png"
        _minimal_png(path)
        extracted = ChatAttachmentTextExtractor().extract(
            storage_path=str(path),
            filename="grafico.png",
            content_type="image/png",
        )

    assert extracted["supported"] is True
    assert "grafico.png" in extracted["content"]


def test_preview_image_kind():
    extracted = {
        "supported": True,
        "content": "[Imagem test.png]",
        "metadata": {
            "extractor": "image_metadata",
            "extension": ".png",
            "width": 800,
            "height": 600,
            "format": "PNG",
        },
    }

    preview = ChatAttachmentPreviewService.build_from_extracted(
        extracted,
        filename="test.png",
    )

    assert preview["kind"] == "image"
    assert preview["width"] == 800
    assert preview["height"] == 600


def test_reading_status_label_indexed():
    assert (
        ChatAttachmentPreviewService.reading_status_label(
            status="indexed",
            parsed=True,
        )
        == "Indexado"
    )
