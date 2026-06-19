from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService
from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService


def test_stamp_bbox_is_bottom_right_per_delpi_norm():
    bbox = ChatDrawingRegionService.stamp_bbox()

    assert ChatDrawingRegionService.stamp_position_is_bottom_right()
    assert bbox[0] >= 0.45
    assert bbox[1] >= 0.5
    assert bbox[2] <= 1.0
    assert bbox[3] <= 1.0


def test_region_bboxes_loaded_from_drawing_stamp_json():
    regions = ChatDrawingRegionService.region_bboxes()

    assert set(regions) >= {"stamp", "title", "bom", "dimensions"}
    assert regions["stamp"] == [0.5, 0.62, 1.0, 1.0]


def test_detail_ocr_config_targets_stamp_and_bom():
    assert set(ChatDrawingRegionService.detail_ocr_regions()) >= {"stamp", "bom"}
    assert ChatDrawingRegionService.detail_zoom_multiplier() >= 2.0
    assert ChatDrawingRegionService.detail_sub_regions("stamp")
    assert ChatDrawingRegionService.detail_sub_regions("bom")


def test_merge_region_ocr_texts_prioritizes_detail_and_dedupes():
    base = "CODIGO DELPI\n90260140"
    detail = "CODIGO DELPI\n90260140\nREV. 04"

    merged = ChatDrawingRegionService.merge_region_ocr_texts(base, detail)

    assert "90260140" in merged
    assert "REV. 04" in merged
    assert merged.splitlines().count("CODIGO DELPI") == 1


def test_merge_region_ocr_texts_returns_detail_when_base_empty():
    assert (
        ChatDrawingRegionService.merge_region_ocr_texts("", "LISTA DE MATERIAIS")
        == "LISTA DE MATERIAIS"
    )


def test_build_region_metadata_includes_detail_pass():
    meta = ChatDrawingRegionService.build_region_metadata(
        region="stamp",
        bbox=[0.5, 0.62, 1.0, 1.0],
        char_count=180,
        engine="tesseract_hybrid",
        detail_pass=True,
        base_char_count=90,
        detail_meta={"zoomMultiplier": 2.5, "detailPass": True},
    )

    assert meta["charCount"] == 180
    assert meta["engine"] == "tesseract_hybrid"
    assert meta["detailPass"] is True
    assert meta["baseCharCount"] == 90
    assert meta["detail"]["zoomMultiplier"] == 2.5


def test_bom_candidate_bboxes_loaded_from_json():
    candidates = ChatDrawingRegionService.bom_candidate_bboxes()

    assert len(candidates) >= 2
    assert all(len(item.get("bbox") or []) == 4 for item in candidates)


def test_ocr_drawing_regions_marks_detail_metadata(monkeypatch):
    class _FakePage:
        rect = type("R", (), {"width": 1000.0, "height": 1400.0})()

    calls: list[str] = []

    def fake_ocr_region_text(*_args, region: str = "", **_kwargs):
        calls.append(f"base:{region or _kwargs.get('bbox')}")
        return "BASE"

    def fake_ocr_region_text_detailed(*_args, region: str, **_kwargs):
        calls.append(f"detail:{region}")
        return f"DETAIL-{region}", {"detailPass": True, "zoomMultiplier": 2.5}

    monkeypatch.setattr(
        ChatDrawingRegionService,
        "ocr_region_text",
        lambda page, *, bbox, matrix, lang, tesseract_config="": fake_ocr_region_text(
            page,
            region=str(bbox),
            bbox=bbox,
            matrix=matrix,
            lang=lang,
        ),
    )
    monkeypatch.setattr(
        ChatDrawingRegionService,
        "ocr_region_text_detailed",
        fake_ocr_region_text_detailed,
    )
    monkeypatch.setattr(
        ChatDrawingRegionService,
        "merge_region_ocr_texts",
        lambda base, detail: f"{base}|{detail}",
    )
    monkeypatch.setattr(
        ChatDocumentVisionBomService,
        "score_bom_text",
        lambda text, **kwargs: 10 if "DETAIL-bom" in text or "10080591" in text else -1,
    )

    texts, metadata = ChatDrawingRegionService.ocr_drawing_regions(
        _FakePage(),
        matrix=object(),
        lang="por",
    )

    assert "stamp" in texts
    assert "bom" in texts
    assert metadata["stamp"]["detailPass"] is True
    assert metadata["bom"]["detailPass"] is True
    assert any(call.startswith("detail:stamp") for call in calls)
    assert any(call.startswith("detail:bom") for call in calls)
