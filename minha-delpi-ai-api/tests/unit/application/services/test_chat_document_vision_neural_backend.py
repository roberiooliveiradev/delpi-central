from unittest.mock import MagicMock, patch

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.infrastructure.config.settings import Settings

_VISION_RUNTIME = {
    "documentVisionEnabled": True,
    "documentVisionAutoVlmFallback": True,
    "documentVisionMaxPages": 10,
    "documentVisionMaxChars": 12000,
}


def _patch_vision_runtime():
    import app.application.services.chat_document_vision_service as vision_mod

    return patch.object(
        vision_mod,
        "_vision_runtime",
        lambda: _VISION_RUNTIME,
        create=True,
    )


def test_docling_backend_falls_back_to_native(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_BACKEND", "docling")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_BACKEND = "docling"

    with _patch_vision_runtime():
        with patch.object(
            ChatDocumentVisionService,
            "_stage_neural_backend",
            return_value={"fullText": "", "warnings": ["docling_not_installed"]},
        ):
            with patch.object(
                ChatDocumentVisionService,
                "_stage_native",
                return_value={
                    "fullText": "TEXTO NATIVO " * 30,
                    "engine": "pypdf",
                    "legible": True,
                    "metadata": {},
                },
            ):
                with patch.object(
                    ChatDocumentVisionService,
                    "_stage_tesseract_pdf",
                    return_value={"fullText": "", "warnings": []},
                ):
                    result = ChatDocumentVisionService.extract_from_storage_path(
                        "/tmp/doc.pdf",
                        filename="doc.pdf",
                        content_type="application/pdf",
                    )

    assert "native" in (result.get("stages") or [])
    assert any(
        "docling_unavailable_fallback_auto" in str(w) for w in (result.get("warnings") or [])
    )


def test_docling_backend_success(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_BACKEND", "docling")
    Settings.CHAT_DOCUMENT_VISION_BACKEND = "docling"

    with _patch_vision_runtime():
        with patch.object(
            ChatDocumentVisionService,
            "_stage_neural_backend",
            return_value={
                "fullText": "LISTA DE MATERIAIS\n90260141 2 TERMINAL",
                "engine": "docling",
                "stages": ["docling"],
                "charCount": 40,
                "legible": True,
                "legibilityScore": 0.5,
                "warnings": [],
            },
        ):
            result = ChatDocumentVisionService.extract_from_storage_path(
                "/tmp/doc.pdf",
                filename="doc.pdf",
                content_type="application/pdf",
            )

    assert result.get("engine") == "docling"
    assert "docling" in (result.get("stages") or [])


def test_ollama_vlm_backend_falls_back_to_auto(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_BACKEND", "ollama_vlm")
    Settings.CHAT_DOCUMENT_VISION_BACKEND = "ollama_vlm"

    with _patch_vision_runtime():
        with patch.object(
            ChatDocumentVisionService,
            "_stage_ollama_vlm",
            return_value={"fullText": "", "warnings": ["ollama_vlm_empty_response"]},
        ):
            with patch.object(
                ChatDocumentVisionService,
                "_stage_native",
                return_value={
                    "fullText": "TEXTO NATIVO " * 30,
                    "engine": "pypdf",
                    "legible": True,
                },
            ):
                with patch.object(
                    ChatDocumentVisionService,
                    "_stage_tesseract_pdf",
                    return_value={"fullText": "", "warnings": []},
                ):
                    result = ChatDocumentVisionService.extract_from_storage_path(
                        "/tmp/doc.pdf",
                        filename="doc.pdf",
                        content_type="application/pdf",
                    )

    assert any(
        "ollama_vlm_unavailable_fallback_auto" in str(w) for w in (result.get("warnings") or [])
    )


def test_ollama_vlm_backend_success(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_BACKEND", "ollama_vlm")
    Settings.CHAT_DOCUMENT_VISION_BACKEND = "ollama_vlm"

    with _patch_vision_runtime():
        with patch.object(
            ChatDocumentVisionService,
            "_stage_ollama_vlm",
            return_value={
                "fullText": "PRODUTO 90260140 REV 01",
                "engine": "ollama_vlm",
                "stages": ["ollama_vlm"],
                "charCount": 24,
                "legible": True,
                "legibilityScore": 0.6,
                "warnings": [],
            },
        ):
            result = ChatDocumentVisionService.extract_from_storage_path(
                "/tmp/doc.pdf",
                filename="doc.pdf",
                content_type="application/pdf",
            )

    assert result.get("engine") == "ollama_vlm"
    assert "ollama_vlm" in (result.get("stages") or [])


def test_stage_docling_converts_when_installed(monkeypatch, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 minimal")

    document = MagicMock()
    document.export_to_markdown.return_value = "LISTA DE MATERIAIS\n90260141 2 PECA"

    conversion = MagicMock()
    conversion.document = document

    converter = MagicMock()
    converter.convert.return_value = conversion

    fake_module = MagicMock()
    fake_module.DocumentConverter.return_value = converter

    with _patch_vision_runtime():
        with patch.dict(
            "sys.modules",
            {"docling": MagicMock(), "docling.document_converter": fake_module},
        ):
            result = ChatDocumentVisionService._stage_docling(
                str(pdf_path),
                filename="sample.pdf",
                warnings=[],
            )

    assert "90260141" in str(result.get("fullText") or "")
    assert result.get("engine") == "docling"


def test_stage_ollama_vlm_calls_chat_api(monkeypatch, tmp_path):
    monkeypatch.setenv("VISION_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_OLLAMA_BASE_URL", "http://ollama.test:11434")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_OLLAMA_MODEL", "qwen2.5vl:7b")

    image_path = tmp_path / "scan.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    gateway = MagicMock()
    gateway.describe.return_value = "CARIMBO 90260140"
    gateway.provider_name.return_value = "ollama"

    image_manager = MagicMock()
    image_manager.__enter__.return_value.convert.return_value = MagicMock()

    with _patch_vision_runtime():
        with patch("PIL.Image.open", return_value=image_manager):
            with patch(
                "app.composition.vision_llm_composer.make_vision_llm_gateway",
                return_value=gateway,
            ):
                with patch.object(
                    ChatDocumentVisionService,
                    "_pil_to_base64_png",
                    return_value="aGVsbG8=",
                ):
                    result = ChatDocumentVisionService._stage_ollama_vlm(
                        str(image_path),
                        filename="scan.png",
                        content_type="image/png",
                    )

    assert "90260140" in str(result.get("fullText") or "")
    gateway.describe.assert_called_once()


def test_stage_ollama_vlm_describe_returns_image_description(monkeypatch, tmp_path):
    monkeypatch.setenv("VISION_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_OLLAMA_BASE_URL", "http://ollama.test:11434")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_OLLAMA_MODEL", "qwen2.5vl:7b")

    image_path = tmp_path / "photo.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    gateway = MagicMock()
    gateway.describe.return_value = "Painel industrial com botões verdes."
    gateway.provider_name.return_value = "ollama"

    image_manager = MagicMock()
    image_manager.__enter__.return_value.convert.return_value = MagicMock()

    with _patch_vision_runtime():
        with patch("PIL.Image.open", return_value=image_manager):
            with patch(
                "app.composition.vision_llm_composer.make_vision_llm_gateway",
                return_value=gateway,
            ):
                with patch.object(
                    ChatDocumentVisionService,
                    "_pil_to_base64_png",
                    return_value="aGVsbG8=",
                ):
                    result = ChatDocumentVisionService._stage_ollama_vlm(
                        str(image_path),
                        filename="photo.png",
                        content_type="image/png",
                        purpose="describe",
                    )

    assert "Painel industrial" in str(result.get("imageDescription") or "")
    assert not str(result.get("fullText") or "").strip()
