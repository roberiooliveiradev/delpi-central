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


def test_build_region_metadata_shape():
    meta = ChatDrawingRegionService.build_region_metadata(
        region="stamp",
        bbox=[0.5, 0.62, 1.0, 1.0],
        char_count=120,
    )

    assert meta["charCount"] == 120
    assert meta["engine"] == "tesseract"
    assert meta["bbox"][1] == 0.62
