from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_typing_correction_fuzzy_lexicon_service import (
    ChatTypingCorrectionFuzzyLexiconService,
)


def test_lexicon_loaded_from_catalog():
    configure_domain_infrastructure_ports()

    assert ChatTypingCorrectionFuzzyLexiconService.term_count() >= 30


def test_fuzzy_match_conservative_gates():
    configure_domain_infrastructure_ports()
    ChatTypingCorrectionFuzzyLexiconService.configure(
        {
            "terms": ["fabril", "producao"],
            "ambiguousTokens": ["num", "como"],
        },
        enabled=True,
    )

    assert ChatTypingCorrectionFuzzyLexiconService._match_token("fabrril") == "fabril"
    assert ChatTypingCorrectionFuzzyLexiconService._match_token("producai") == "producao"
    assert ChatTypingCorrectionFuzzyLexiconService._match_token("como") is None
    assert ChatTypingCorrectionFuzzyLexiconService._match_token("num") is None
    assert ChatTypingCorrectionFuzzyLexiconService._match_token("fab") is None

    from app.infrastructure.content.content_service import ContentService

    ChatTypingCorrectionFuzzyLexiconService.configure(
        ContentService.load_json("assistant/typing_correction_lexicon"),
        enabled=True,
    )

def test_apply_to_text_corrects_tokens_and_preserves_codes():
    configure_domain_infrastructure_ports()
    ChatTypingCorrectionFuzzyLexiconService.configure(
        {
            "terms": ["estrutura", "estoque"],
            "ambiguousTokens": [],
            "protectedPortugueseTokens": [],
        },
        enabled=True,
    )

    result = ChatTypingCorrectionFuzzyLexiconService.apply_to_text(
        "qual a estrutra do 90260148?"
    )
    assert "estrutura" in result
    assert "estrutra" not in result
    assert "90260148" in result

    from app.infrastructure.content.content_service import ContentService

    ChatTypingCorrectionFuzzyLexiconService.configure(
        ContentService.load_json("assistant/typing_correction_lexicon"),
        enabled=True,
    )
