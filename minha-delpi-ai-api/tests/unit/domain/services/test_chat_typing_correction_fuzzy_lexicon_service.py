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
