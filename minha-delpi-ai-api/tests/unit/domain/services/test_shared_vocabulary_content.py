from app.domain.services.chat_date_range_vocabulary_service import (
    ChatDateRangeVocabularyService,
)
from app.domain.services.chat_operational_pipeline_vocabulary_service import (
    ChatOperationalPipelineVocabularyService,
)
from app.domain.services.chat_session_vocabulary_service import (
    ChatSessionVocabularyService,
)
from app.domain.services.chat_term_extraction_vocabulary_service import (
    ChatTermExtractionVocabularyService,
)


def test_term_extraction_stopwords_loaded_from_json():
    assert "voce" in ChatTermExtractionVocabularyService.terms("stopwords")


def test_session_topic_change_markers_loaded():
    assert ChatSessionVocabularyService.terms("topicChangeMarkers")


def test_operational_pipeline_terms_loaded():
    assert "estoque" in ChatOperationalPipelineVocabularyService.terms("operationalTerms")
    assert "explique" in ChatOperationalPipelineVocabularyService.terms("documentalTerms")


def test_date_range_vocabulary_has_months_and_phrases():
    assert ChatDateRangeVocabularyService.months_pt()["janeiro"] == 1
    assert ChatDateRangeVocabularyService.terms("periodMetricTerms")
    assert ChatDateRangeVocabularyService.week_offset_phrases().get(-1)
    assert ChatDateRangeVocabularyService.weekdays_pt()["segunda"] == 0
    assert ChatDateRangeVocabularyService.temporal_range_markers()


def test_date_range_vocabulary_includes_brazilian_temporal_variants():
    current_week = ChatDateRangeVocabularyService.week_offset_phrases().get(0, ())
    assert "essa semana" in current_week
    assert "nessa semana" in current_week

    two_weeks_ago = ChatDateRangeVocabularyService.week_offset_phrases().get(-2, ())
    assert "semana antepassada" in two_weeks_ago

    current_month = ChatDateRangeVocabularyService.terms("currentMonthPhrases")
    assert "esse mes" in current_month
    assert "nesse mes" in current_month

    current_year = ChatDateRangeVocabularyService.terms("currentYearPhrases")
    assert "esse ano" in current_year
    assert "desse ano" in current_year

    assert ChatDateRangeVocabularyService.terms("nextYearPhrases")
    assert ChatDateRangeVocabularyService.terms("nextQuarterPhrases")
    assert ChatDateRangeVocabularyService.terms("currentSemesterPhrases")
    assert ChatDateRangeVocabularyService.fixed_semester_phrases().get(1)

    markers = ChatDateRangeVocabularyService.temporal_range_markers()
    assert "agora" in markers
    assert "semana retrasada" in markers
    assert "proximo semestre" in markers


def test_canvas_transform_vocabulary_loaded():
    from app.domain.services.chat_canvas_transform_vocabulary_service import (
        ChatCanvasTransformVocabularyService,
    )

    assert ChatCanvasTransformVocabularyService.kind_terms("checklist")
    assert ChatCanvasTransformVocabularyService.template("checklistHeader")


def test_web_search_vocabulary_loaded():
    from app.domain.services.chat_web_search_vocabulary_service import (
        ChatWebSearchVocabularyService,
    )

    assert ChatWebSearchVocabularyService.terms("explicitRequest", "triggerTerms")
    assert ChatWebSearchVocabularyService.terms("planning", "deepTerms")
