from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
    ChatOperationalLlmSynthesisContextContentService,
)
from app.domain.services.chat_response_mode_synthesis_quality_content_service import (
    ChatResponseModeSynthesisQualityContentService,
)

configure_domain_infrastructure_ports()


def test_coherence_checks_load_from_json():
    assert (
        ChatResponseModeSynthesisQualityContentService.coherence_gap("emptyAnswer")
        == "resposta vazia após síntese LLM"
    )
    assert ChatResponseModeSynthesisQualityContentService.coherence_limit_int(
        "repeatedSentenceMinChars",
    ) == 48
    assert ChatResponseModeSynthesisQualityContentService.coherence_limit_int(
        "sparseListMinLines",
    ) == 2
    assert len(ChatResponseModeSynthesisQualityContentService.sparse_list_patterns()) == 2


def test_answer_enrichment_dedupe_limits_load_from_json():
    assert ChatOperationalLlmSynthesisContextContentService.dedupe_paragraph_key_chars() == 160
    assert ChatOperationalLlmSynthesisContextContentService.dedupe_paragraph_min_key_chars() == 40
    assert ChatOperationalLlmSynthesisContextContentService.dedupe_sentence_key_chars() == 160
    assert ChatOperationalLlmSynthesisContextContentService.dedupe_sentence_min_key_chars() == 48


def test_quality_gaps_and_ladder_load_from_json():
    assert (
        ChatResponseModeSynthesisQualityContentService.gap(
            "template",
            "clone",
            similarity=0.9,
            max_similarity=0.72,
        )
        == "resposta reproduz o template operacional (similaridade 0.90 >= 0.72)"
    )
    assert ChatResponseModeSynthesisQualityContentService.pipeline_expected_effect("fast") == (
        "llm_synthesis_brief"
    )
    assert ChatResponseModeSynthesisQualityContentService.mode_ladder_required_pairs() == (
        ("fast", "normal"),
        ("normal", "thinker"),
    )
    assert len(ChatResponseModeSynthesisQualityContentService.numbered_run_patterns()) == 2
