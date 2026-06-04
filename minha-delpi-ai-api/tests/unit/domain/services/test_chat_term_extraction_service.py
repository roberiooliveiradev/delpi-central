from app.domain.services.chat_term_extraction_service import (
    ChatTermExtractionService,
)


def test_detects_definition_question():
    assert ChatTermExtractionService.detect_definition_question("o que é PKCE?") == "PKCE"
    assert ChatTermExtractionService.detect_definition_question("o que significa RAG") == "RAG"
    assert ChatTermExtractionService.detect_definition_question("defina CFW500") == "CFW500"
    assert (
        ChatTermExtractionService.detect_definition_question("significado de modo lousa")
        == "modo lousa"
    )


def test_ignores_non_definition_questions():
    assert ChatTermExtractionService.detect_definition_question("qual o faturamento?") is None
    assert ChatTermExtractionService.detect_definition_question("oi, tudo bem?") is None
    assert ChatTermExtractionService.detect_definition_question("o que é isso") is None


def test_classify_unknown_term():
    assert ChatTermExtractionService.classify_unknown_term("PKCE") == "acronym"
    assert ChatTermExtractionService.classify_unknown_term("CFW500") == "product_code"
    assert ChatTermExtractionService.classify_unknown_term("10080001") == "internal_code"
    assert ChatTermExtractionService.classify_unknown_term("reranking") == "technical"
    assert ChatTermExtractionService.classify_unknown_term("modo lousa") == "phrase"


def test_is_web_researchable():
    assert ChatTermExtractionService.is_web_researchable("PKCE") is True
    assert ChatTermExtractionService.is_web_researchable("CFW500") is True
    assert ChatTermExtractionService.is_web_researchable("reranking") is True
    assert ChatTermExtractionService.is_web_researchable("10080001") is False
