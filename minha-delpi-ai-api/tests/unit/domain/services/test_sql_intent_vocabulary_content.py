from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
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
    """Programação do dia com código de família pode ir para REST; frases no JSON ainda existem."""
    phrases = ChatSqlIntentVocabularyService.terms(
        "operationalIntent",
        "productionPhrases",
    )
    assert any("programados para produzir" in str(p) for p in phrases)


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


def test_sql_authoring_intro_is_domain_neutral():
    from app.domain.services.chat_assistant_content_service import (
        invalidate_assistant_content_cache,
    )
    from app.domain.services.chat_advanced_sql_specialist_service import (
        ChatAdvancedSqlSpecialistService,
    )
    from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prose_formatting_service import (
        ChatAdvancedSqlSpecialistProseFormattingService,
    )
    from app.infrastructure.content.content_service import ContentService

    ContentService.clear_cache()
    invalidate_assistant_content_cache("sql_intent_vocabulary")
    ChatAdvancedSqlSpecialistProseFormattingService._sql_authoring_intro_re.cache_clear()

    intro = ChatSqlIntentVocabularyService.text(
        "advancedSqlSpecialist",
        "sqlAuthoringIntro",
    )
    assert "SA1010" not in intro
    assert "SB1010" not in intro
    assert "010" in intro
    formatted = ChatAdvancedSqlSpecialistService.format_sql_authoring_answer(
        "```sql\nSELECT TOP 10 B1_COD FROM SB1010\n```"
    )
    assert "SA1010" not in formatted.split("```sql")[0]


def test_advanced_sql_specialist_vocabulary_loaded():
    assert ChatSqlIntentVocabularyService.terms(
        "advancedSqlSpecialist",
        "activationTerms",
    )
    assert ChatSqlIntentVocabularyService.text(
        "advancedSqlSpecialist",
        "sqlAuthoringIntro",
    )
    assert ChatSqlIntentVocabularyService.text(
        "advancedSqlSpecialist",
        "authoringHints",
        "productCadastro",
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
