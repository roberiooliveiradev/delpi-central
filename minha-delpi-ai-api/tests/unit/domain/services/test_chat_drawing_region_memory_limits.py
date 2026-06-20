from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService


def test_bom_candidate_bboxes_respects_config_limit(monkeypatch):
    monkeypatch.setattr(
        "app.domain.services.chat_drawing_region_service.ChatDocumentVisionContentService.pdf_region_ocr_max_bom_candidates",
        staticmethod(lambda: 2),
    )

    candidates = ChatDrawingRegionService.bom_candidate_bboxes()

    assert len(candidates) <= 2
