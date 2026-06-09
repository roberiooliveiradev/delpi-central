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
