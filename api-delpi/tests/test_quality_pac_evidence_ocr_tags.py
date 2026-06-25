from app.domain.services.quality_action_plans.pac_evidence_ocr_tag_suggestion_service import (
    PacEvidenceOcrTagSuggestionService,
)


def test_suggest_tags_from_ocr_text():
    result = PacEvidenceOcrTagSuggestionService.suggest(
        ocr_text="oxidação em parafusos produto 90110001",
        file_name="nc.jpg",
    )

    assert "oxidação" in result["suggested_symptom_tags"]
    assert "90110001" in result["suggested_product_codes"]
