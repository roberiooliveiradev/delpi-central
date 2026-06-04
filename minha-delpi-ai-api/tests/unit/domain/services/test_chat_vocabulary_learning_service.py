from app.domain.services.chat_vocabulary_learning_service import (
    ChatVocabularyLearningService,
)


def test_detect_explicit_definition_when_phrase():
    result = ChatVocabularyLearningService.detect_explicit_definition(
        "Quando eu falar TRANSFORMA, estou falando do módulo de engenharia"
    )

    assert result is not None
    assert result["candidateType"] == "term_definition"
    assert result["term"] == "TRANSFORMA"
    assert result["proposedMeaning"] == "módulo de engenharia"
    assert result["confidence"] >= 0.85
    assert result["source"] == "user_explicit_definition"


def test_detect_explicit_definition_significa():
    result = ChatVocabularyLearningService.detect_explicit_definition(
        "lousa significa o canvas do chat"
    )

    assert result is not None
    assert result["term"].lower() == "lousa"
    assert result["proposedMeaning"] == "o canvas do chat"


def test_detect_explicit_definition_ignores_long_term():
    result = ChatVocabularyLearningService.detect_explicit_definition(
        "essa frase enorme que claramente nao e um termo curto significa outra coisa qualquer"
    )

    assert result is None


def test_detect_explicit_definition_none_for_plain_question():
    assert (
        ChatVocabularyLearningService.detect_explicit_definition(
            "qual o estoque do produto 10080001?"
        )
        is None
    )


def test_build_normalization_candidate_keeps_raw_form():
    result = ChatVocabularyLearningService.build_normalization_candidate(
        "como vc s chama?",
        source="feedback",
        base_confidence=0.5,
    )

    assert result is not None
    assert result["candidateType"] == "normalization_rule"
    assert result["inputText"] == "como vc s chama?"
    # Termo sem acento/minúsculo, correção fica para o admin definir.
    assert result["term"] == "como vc s chama?"
    assert result["proposedRule"] is None
    assert result["confidence"] == 0.5


def test_classify_term():
    assert ChatVocabularyLearningService.classify_term("LMP") == "abbreviation"
    assert ChatVocabularyLearningService.classify_term("vc") == "abbreviation"
    assert ChatVocabularyLearningService.classify_term("modulo de engenharia") == "phrase"
    assert ChatVocabularyLearningService.classify_term("prduto") == "typo"
