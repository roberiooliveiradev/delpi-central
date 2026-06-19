"""Análise de layout de página — XY-Cut e regiões semânticas DELPI."""

from PIL import Image, ImageDraw

from app.domain.services.chat_drawing_page_layout_analysis_service import (
    ChatDrawingPageLayoutAnalysisService,
)
from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService


def _synthetic_delpi_page() -> Image.Image:
    image = Image.new("RGB", (1000, 1400), "white")
    draw = ImageDraw.Draw(image)

    draw.rectangle((20, 20, 520, 420), outline="black", width=2)
    draw.text((40, 40), "LISTA DE MATERIAIS", fill="black")
    draw.text((40, 80), "10081867  2000", fill="black")
    draw.text((40, 110), "50215425  1", fill="black")

    draw.rectangle((250, 20, 750, 120), outline="black", width=1)
    draw.text((280, 50), "CHICOTE DE LIGACAO", fill="black")

    draw.rectangle((40, 200, 960, 820), outline="black", width=1)
    draw.line((100, 300, 900, 300), fill="black", width=1)
    draw.text((120, 320), "140", fill="black")

    draw.rectangle((520, 900, 980, 1380), outline="black", width=2)
    draw.text((540, 920), "CODIGO DELPI", fill="black")
    draw.text((540, 950), "90264227", fill="black")
    draw.text((540, 980), "REV. 02", fill="black")

    return image


def test_xy_cut_detects_stamp_bom_and_title_regions():
    result = ChatDrawingPageLayoutAnalysisService.analyze_page_image(_synthetic_delpi_page())

    assert result.algorithm == "xy_cut_semantic_v1"
    assert result.blocks
    assert "stamp" in result.semantic_regions
    assert "bom" in result.semantic_regions

    stamp = result.semantic_regions["stamp"]
    bom = result.semantic_regions["bom"]

    assert stamp[0] >= 0.45
    assert stamp[1] >= 0.55
    assert bom[0] <= 0.55
    assert bom[1] <= 0.45


def test_layout_metadata_exposed_by_region_service(monkeypatch):
    class _FakePage:
        rect = type("R", (), {"width": 1000.0, "height": 1400.0})()

    monkeypatch.setattr(
        ChatDrawingPageLayoutAnalysisService,
        "analyze_fitz_page",
        lambda *_args, **_kwargs: ChatDrawingPageLayoutAnalysisService.analyze_page_image(
            _synthetic_delpi_page()
        ),
    )
    monkeypatch.setattr(
        ChatDrawingRegionService,
        "_ocr_region_bundle",
        lambda *_args, **_kwargs: ("TEXTO", {"bbox": [0, 0, 1, 1], "charCount": 5, "engine": "mock"}),
    )
    monkeypatch.setattr(
        ChatDrawingRegionService,
        "_ocr_bom_region",
        lambda *_args, **_kwargs: (
            "LISTA DE MATERIAIS",
            [0.0, 0.0, 0.55, 0.35],
            {"bbox": [0.0, 0.0, 0.55, 0.35], "charCount": 18, "engine": "mock"},
        ),
    )

    _texts, metadata = ChatDrawingRegionService.ocr_drawing_regions(
        _FakePage(),
        matrix=None,
        lang="por",
    )

    assert _texts.get("bom")
    assert metadata.get("_layoutAnalysis", {}).get("algorithm") == "xy_cut_semantic_v1"


def test_resolve_semantic_bboxes_falls_back_when_disabled(monkeypatch):
    monkeypatch.setattr(
        ChatDrawingPageLayoutAnalysisService,
        "_enabled",
        classmethod(lambda cls: False),
    )

    bboxes, meta = ChatDrawingPageLayoutAnalysisService.resolve_semantic_bboxes(
        page=object(),
        matrix=None,
    )

    assert bboxes["stamp"] == [0.5, 0.62, 1.0, 1.0]
    assert meta == {}
