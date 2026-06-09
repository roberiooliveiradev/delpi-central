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
        "shared",
        "previousQueryTerms",
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


def test_column_definitions_loaded_from_json():
    production = ChatSqlIntentVocabularyService.column_definitions("SC2010")

    assert "filial" in production
    assert "FILIAL" in production["filial"]["select"]


def test_advanced_sql_specialist_vocabulary_loaded():
    assert ChatSqlIntentVocabularyService.terms(
        "advancedSqlSpecialist",
        "activationTerms",
    )
    assert ChatSqlIntentVocabularyService.text(
        "advancedSqlSpecialist",
        "sqlAuthoringIntro",
    )
    assert ChatSqlIntentVocabularyService.mode_pattern_map().get("review")
    assert ChatSqlIntentVocabularyService.planner_hints()


def test_shared_terms_merged_without_duplication():
    merged = ChatSqlIntentVocabularyService.incremental_authoring_terms()

    assert "consulta anterior" in merged
    assert "agrupar por" in merged
    assert "primeiros" in merged
    assert merged.count("consulta anterior") == 1

    group_by = ChatSqlIntentVocabularyService.group_by_terms()

    assert "agrupado por filial" not in group_by
    assert "agrupado por" in group_by
    assert group_by.count("agrupar por") == 1


def test_query_pattern_advisor_reads_guidance_from_json():
    from app.domain.services.chat_sql_query_pattern_advisor_service import (
        ChatSqlQueryPatternAdvisorService,
    )

    result = ChatSqlQueryPatternAdvisorService.recommend(
        "ranking top 10 clientes por categoria"
    )

    assert result["patterns"]
    assert "window_rank" in result["hints"]
