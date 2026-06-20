"""Sugestões de perguntas por rota no composer."""

from app.domain.services.chat_composer_route_question_suggestion_service import (
    ChatComposerRouteQuestionSuggestionService,
)
from app.domain.services.chat_typing_correction_fuzzy_lexicon_service import (
    ChatTypingCorrectionFuzzyLexiconService,
)
from app.domain.services.chat_typing_correction_service import (
    ChatTypingCorrectionService,
)
from app.infrastructure.content.content_service import ContentService


def test_analise_desenho_is_not_fuzzy_corrected_to_analyser():
    ChatTypingCorrectionFuzzyLexiconService.configure(
        ContentService.load_json("assistant/typing_correction_lexicon"),
        enabled=True,
    )

    result = ChatTypingCorrectionService.suggest("analise o desenho")

    assert result["hasSuggestions"] is False
    assert result["corrected"] == "analise o desenho"


def test_partial_analise_offers_drawing_route_questions():
    suggestions = ChatComposerRouteQuestionSuggestionService.suggest("analise")

    assert suggestions
    assert any("desenho" in item["query"] for item in suggestions)
    assert all(item["query"] != "analise" for item in suggestions)


def test_complete_drawing_query_does_not_repeat_route_question():
    suggestions = ChatComposerRouteQuestionSuggestionService.suggest("analise o desenho")

    assert not any(item["query"] == "analise o desenho" for item in suggestions)


def test_estouque_still_offers_typo_rule_suggestion():
    result = ChatTypingCorrectionService.suggest("estouque do produto 90262404")

    assert result["hasSuggestions"] is True
    assert "estoque" in result["corrected"]
