from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_pdf_region_ocr_engine_service import (
    ChatPdfRegionOcrEngineService,
)


def test_bom_region_uses_tesseract_and_easyocr_only():
    engines = ChatDocumentVisionContentService.pdf_bom_region_ocr_engines()

    assert engines == ("tesseract", "easyocr")


def test_region_override_keeps_bom_multi_engine_fusion(monkeypatch):
    calls: list[str] = []

    def fake_detailed(engine, image, *, lang, tesseract_config):
        del image, lang, tesseract_config
        calls.append(engine)
        return {"text": "90264227", "codeTokens": []}

    monkeypatch.setattr(
        ChatPdfRegionOcrEngineService,
        "_run_engine_detailed",
        staticmethod(fake_detailed),
    )

    with ChatPdfRegionOcrEngineService.region_ocr_engines_override(["tesseract"]):
        ChatPdfRegionOcrEngineService.recognize(
            object(),
            lang="por+eng",
            region="bom",
        )

    assert calls == ["tesseract", "easyocr"]


def test_region_override_limits_non_bom_regions_to_tesseract_only(monkeypatch):
    calls: list[str] = []

    def fake_detailed(engine, image, *, lang, tesseract_config):
        del image, lang, tesseract_config
        calls.append(engine)
        return {"text": "REV 02", "codeTokens": []}

    monkeypatch.setattr(
        ChatPdfRegionOcrEngineService,
        "_run_engine_detailed",
        staticmethod(fake_detailed),
    )

    with ChatPdfRegionOcrEngineService.region_ocr_engines_override(["tesseract"]):
        ChatPdfRegionOcrEngineService.recognize(
            object(),
            lang="por+eng",
            region="stamp",
        )

    assert calls == ["tesseract"]


def test_recognize_bom_uses_weighted_fusion(monkeypatch):
    calls: list[str] = []

    def fake_detailed(engine, image, *, lang, tesseract_config):
        del image, lang, tesseract_config
        calls.append(engine)

        if engine == "tesseract":
            return {
                "text": "50215426 | 10440154",
                "codeTokens": [
                    {
                        "code": "10440154",
                        "confidence": 0.6,
                        "lineIndex": 0,
                        "codeIndex": 1,
                    }
                ],
            }

        return {
            "text": "50215426 | 10440134",
            "codeTokens": [
                {
                    "code": "10440134",
                    "confidence": 0.9,
                    "lineIndex": 0,
                    "codeIndex": 1,
                }
            ],
        }

    monkeypatch.setattr(
        ChatPdfRegionOcrEngineService,
        "_run_engine_detailed",
        staticmethod(fake_detailed),
    )

    result = ChatPdfRegionOcrEngineService.recognize(
        object(),
        lang="por+eng",
        region="bom",
    )

    assert set(calls) == {"tesseract", "easyocr"}
    assert result["fusion"] == "bom_weighted"
    assert "10440134" in result["text"]
    assert "10440154" not in result["text"]
