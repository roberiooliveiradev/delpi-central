from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
)
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)


def test_sql_intent_vocabulary_bundle_has_core_sections():
    assert ChatAssistantContentService.list(
        "sql_intent_vocabulary",
        "operationalIntent",
        "productionPhrases",
    )
    assert ChatAssistantContentService.list(
        "sql_intent_vocabulary",
        "queryRefinement",
        "showQueryTerms",
    )
    assert ChatAssistantContentService.list(
        "sql_intent_vocabulary",
        "dynamicColumnRefinement",
        "groupByTerms",
    )
    assert ChatAssistantContentService.list(
        "sql_intent_vocabulary",
        "resultAnalyzer",
        "emptyRecoveryFollowUps",
    )


def test_production_intent_reads_programados_para_produzir_from_json():
    assert ChatSqlOperationalIntentService.requires_production_sql_knowledge(
        "quais os 9026 estão programados para produzir hoje?"
    )


def test_dynamic_column_synonyms_loaded_from_json():
    synonyms = ChatSqlIntentVocabularyService.synonym_map(
        "dynamicColumnRefinement",
        "columnSynonyms",
    )

    assert "filial" in synonyms
    assert "COD_PRODUTO" in synonyms["produto"]


def test_advanced_sql_specialist_vocabulary_loaded():
    assert ChatSqlIntentVocabularyService.terms(
        "advancedSqlSpecialist",
        "activationTerms",
    )
    assert ChatSqlIntentVocabularyService.mode_pattern_map().get("review")
    assert ChatSqlIntentVocabularyService.planner_hints()


def test_query_pattern_advisor_reads_guidance_from_json():
    from app.domain.services.chat_sql_query_pattern_advisor_service import (
        ChatSqlQueryPatternAdvisorService,
    )

    result = ChatSqlQueryPatternAdvisorService.recommend(
        "ranking top 10 clientes por categoria"
    )

    assert result["patterns"]
    assert "window_rank" in result["hints"]
