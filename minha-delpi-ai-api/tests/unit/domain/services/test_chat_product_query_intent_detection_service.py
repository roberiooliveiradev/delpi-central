from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_detection_service import (
    ChatProductQueryIntentDetectionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


def test_detect_pipeline_loaded_from_json():
    pipeline = ChatProductQueryIntentDetectionService._detect_pipeline()

    assert pipeline
    assert pipeline[0]["probe"] == "drawingAnalysis"
    assert pipeline[-1]["predicate"] == "descriptionQuestion"


def test_refine_pipeline_loaded_from_json():
    pipeline = ChatProductQueryIntentDetectionService._refinement_pipeline()

    assert pipeline
    assert pipeline[-1]["probe"] == "singleScopeIntent"


def test_detect_matches_legacy_service():
    message = "estoque do produto 90260142"

    assert (
        ChatProductQueryIntentDetectionService.detect(message)
        == ChatProductQueryIntent.STOCK
    )


def test_refine_matches_legacy_service():
    message = "estoque do produto 90260142"

    assert (
        ChatProductQueryIntentDetectionService.refine_operational_intent_from_full(message)
        == ChatProductQueryIntent.STOCK
    )


def test_detect_playbook_scope_before_stock_sub_intent():
    message = "status fabril do produto 90269002 hoje"

    assert (
        ChatProductQueryIntentDetectionService.detect(message)
        == ChatProductQueryIntent.FULL
    )


def test_single_scope_intent_from_json_map():
    message = "estrutura do produto 90260142"

    assert (
        ChatProductQueryIntentDetectionService.refine_operational_intent_from_full(message)
        == ChatProductQueryIntent.STRUCTURE
    )


def test_detect_structure_with_operational_typography_typo():
    """Tipografia operacional (estrutra) deve resolver via fuzzy no normalize — não unclear."""
    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_typing_correction_fuzzy_lexicon_service import (
        ChatTypingCorrectionFuzzyLexiconService,
    )
    from app.infrastructure.content.content_service import ContentService

    configure_domain_infrastructure_ports()
    message = "qual a estrutra do 90260148?"

    normalized = ChatMessageNormalizationService.normalize_for_matching(message)
    assert "estrutura" in normalized
    assert "estrutra" not in normalized

    assert (
        ChatProductQueryIntentDetectionService.detect(message)
        == ChatProductQueryIntent.STRUCTURE
    )
    assert (
        ChatProductQueryIntentDetectionService.refine_operational_intent_from_full(message)
        == ChatProductQueryIntent.STRUCTURE
    )

    # Sem fuzzy no matching, tipografia residual não vira structure (regressão de qualidade).
    ChatTypingCorrectionFuzzyLexiconService.configure(
        {"terms": ["estrutura"], "ambiguousTokens": [], "protectedPortugueseTokens": []},
        enabled=False,
    )
    assert "estrutra" in ChatMessageNormalizationService.normalize_for_matching(message)
    assert (
        ChatProductQueryIntentDetectionService.detect(message)
        != ChatProductQueryIntent.STRUCTURE
    )

    # Restaura léxico completo (configure_domain_infrastructure_ports é no-op após 1ª chamada).
    ChatTypingCorrectionFuzzyLexiconService.configure(
        ContentService.load_json("assistant/typing_correction_lexicon"),
        enabled=True,
    )
    assert ChatTypingCorrectionFuzzyLexiconService.is_enabled()
    assert (
        ChatProductQueryIntentDetectionService.detect(message)
        == ChatProductQueryIntent.STRUCTURE
    )

def test_mixed_documental_operational_probe():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "explique a politica de estoque do produto"
    )

    assert ChatProductQueryIntentDetectionService.looks_like_mixed_documental_operational(
        normalized
    )


def test_intent_probes_cover_detect_pipeline():
    probes = ChatAssistantContentService.get_node(
        ChatProductQueryIntentDetectionService.BUNDLE,
        "intentProbes",
    )

    assert isinstance(probes, dict)

    for step in ChatProductQueryIntentDetectionService._detect_pipeline():
        probe = str(step.get("probe") or "").strip()

        if probe:
            assert probe in probes


def test_product_summary_probe_uses_json_matcher():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "resumo do produto 90260142"
    )

    assert ChatProductQueryIntentDetectionService.looks_like_product_summary_question(
        normalized
    )
