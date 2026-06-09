from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_analysis_intent_vocabulary_service import (
    ChatAnalysisIntentVocabularyService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


def test_analysis_intent_vocabulary_bundle_has_core_sections():
    assert ChatAnalysisIntentVocabularyService.terms("comparisonTerms")
    assert ChatAnalysisIntentVocabularyService.terms("dataInterpretationTerms")
    assert ChatAnalysisIntentVocabularyService.terms("sqlResultInterpretationTerms")


def test_comparison_intent_reads_from_json():
    assert ChatAnalysisIntentService.is_comparison_or_insight_request(
        "compare as duas estruturas e traga insights"
    )
