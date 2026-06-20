import pytest

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_typing_correction_fuzzy_lexicon_service import (
    ChatTypingCorrectionFuzzyLexiconService,
)
from app.domain.services.chat_typing_correction_service import (
    ChatTypingCorrectionService,
)
from app.infrastructure.content.content_service import ContentService
from tests.fixtures.chat_typing_correction_cases import TYPING_CORRECTION_CASES


@pytest.fixture(autouse=True)
def _enable_fuzzy_lexicon(monkeypatch):
    ChatTypingCorrectionFuzzyLexiconService.configure(
        ContentService.load_json("assistant/typing_correction_lexicon"),
        enabled=True,
    )

    def _is_enabled_for_tests(cls) -> bool:
        return cls._enabled

    monkeypatch.setattr(
        ChatTypingCorrectionFuzzyLexiconService,
        "is_enabled",
        classmethod(_is_enabled_for_tests),
    )
    yield


@pytest.fixture(autouse=True)
def _clear_learned_rules():
    ChatMessageNormalizationService.clear_learned_rules()
    yield
    ChatMessageNormalizationService.clear_learned_rules()


@pytest.mark.parametrize("case", TYPING_CORRECTION_CASES, ids=lambda case: case.id)
def test_playbook_typing_correction_cases(case):
    result = ChatTypingCorrectionService.suggest(case.text)

    assert result["hasSuggestions"] is case.expect_suggestions

    if case.expect_unchanged:
        assert result["corrected"] == case.text

    for token in case.expect_in_corrected:
        assert token in result["corrected"]

    for token in case.expect_not_in_corrected:
        assert token not in result["corrected"]

    if case.max_changes is not None:
        assert len(result["changes"]) <= case.max_changes


def test_t1_suggests_estoque_preserves_product_code():
    result = ChatTypingCorrectionService.suggest("estouque do produto 90262404")

    assert result["hasSuggestions"] is True
    assert result["corrected"] == "estoque do produto 90262404"
    assert "90262404" in result["corrected"]
    assert any(change["to"] == "estoque" for change in result["changes"])


def test_t2_filial_code_intact():
    result = ChatTypingCorrectionService.suggest("qual o status fabril filial 01")

    assert "01" in result["corrected"]
    protected = result["protectedSpans"]
    assert not any(
        span["start"] <= result["corrected"].index("01") < span["end"]
        for span in protected
        if "01" in result["corrected"]
    ) or "01" in result["corrected"]


def test_t3_no_suggestion_after_corrija_marker():
    result = ChatTypingCorrectionService.suggest("corrija: estouque baixo")

    assert result["hasSuggestions"] is False
    assert result["corrected"] == "corrija: estouque baixo"


def test_t4_mention_intact():
    result = ChatTypingCorrectionService.suggest("@Agente estouque")

    assert result["corrected"].startswith("@Agente")
    assert "estoque" in result["corrected"]


def test_t5_learned_rule_matches_normalization():
    ChatMessageNormalizationService.set_learned_rules([("fabrik", "fabrica")])

    normalized = ChatMessageNormalizationService.normalize_for_matching("fabrik 01")
    suggested = ChatTypingCorrectionService.suggest("fabrik 01")

    assert "fabrica" in normalized
    assert suggested["hasSuggestions"] is True
    assert "fabrica" in suggested["corrected"]


def test_t7_no_suggestion_in_sql():
    result = ChatTypingCorrectionService.suggest("SELECT * FROM SB1")

    assert result["hasSuggestions"] is False


def test_max_three_substitutions():
    result = ChatTypingCorrectionService.suggest(
        "estouque do prduto na filail com qtd baixa"
    )

    assert len(result["changes"]) <= ChatTypingCorrectionService.MAX_CHANGES


def test_backtick_span_protected():
    result = ChatTypingCorrectionService.suggest("consulte `estouque` do produto 10080001")

    assert "`estouque`" in result["corrected"]


def test_empty_text():
    result = ChatTypingCorrectionService.suggest("   ")

    assert result["hasSuggestions"] is False


def test_t8_fuzzy_lexicon_suggests_fabril():
    result = ChatTypingCorrectionService.suggest("status fabrril filial 01")

    assert result["hasSuggestions"] is True
    assert "fabril" in result["corrected"]
    assert "01" in result["corrected"]
    assert any(change["kind"] == "fuzzy_lexicon" for change in result["changes"])


def test_t9_ambiguous_tokens_not_fuzzy_corrected():
    result = ChatTypingCorrectionService.suggest("como para que sim")

    assert result["hasSuggestions"] is False


def test_fuzzy_disabled_without_flag():
    ChatTypingCorrectionFuzzyLexiconService.configure(
        ContentService.load_json("assistant/typing_correction_lexicon"),
        enabled=False,
    )

    result = ChatTypingCorrectionService.suggest("status fabrril filial 01")

    assert result["hasSuggestions"] is False


def test_fuzzy_skips_protected_portuguese_tokens():
    ChatTypingCorrectionFuzzyLexiconService.configure(
        {
            "terms": ["analyser"],
            "protectedPortugueseTokens": ["analise"],
            "ambiguousTokens": [],
        },
        enabled=True,
    )

    assert ChatTypingCorrectionFuzzyLexiconService._match_token("analise") is None


def test_analise_desenho_is_not_corrected_to_analyser():
    result = ChatTypingCorrectionService.suggest("analise o desenho")

    assert result["hasSuggestions"] is False
    assert result["corrected"] == "analise o desenho"
