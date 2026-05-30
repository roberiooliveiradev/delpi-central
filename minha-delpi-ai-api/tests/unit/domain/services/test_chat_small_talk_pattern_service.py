import pytest

from app.domain.services.chat_small_talk_pattern_service import ChatSmallTalkPatternService


@pytest.mark.parametrize(
    "message,expected",
    [
        ("ola", "greeting"),
        ("olá, tudo bem?", "greeting"),
        ("bom dia", "greeting"),
        ("fala ai", "greeting"),
        ("salve", "greeting"),
        ("tudo bem", "wellbeing"),
        ("como vc esta", "wellbeing"),
        ("tudo de boa", "wellbeing"),
        ("obrigado", "thanks"),
        ("muito obrigada", "thanks"),
        ("vlw", "thanks"),
        ("desculpa", "apology"),
        ("foi mal", "apology"),
        ("show", "praise"),
        ("massa", "praise"),
        ("parabens", "praise"),
        ("ate mais", "farewell"),
        ("ate logo", "farewell"),
        ("a gente se ve", "farewell"),
        ("tchau", "farewell"),
        ("ok", "ack"),
        ("entendi", "ack"),
        ("beleza entao", "ack"),
        ("kkk", "laughter"),
        ("hahaha", "laughter"),
    ],
)
def test_small_talk_pattern_categories(message: str, expected: str):
    assert ChatSmallTalkPatternService.match_category(message) == expected


@pytest.mark.parametrize(
    "message",
    [
        "sim quero estoque",
        "estoque do produto 10080047",
        "mostre o relatorio",
        "obrigado por listar os pedidos de hoje",
    ],
)
def test_small_talk_excludes_operational_or_compound(message: str):
    assert ChatSmallTalkPatternService.match_category(message) is None


def test_ack_requires_exact_match():
    assert ChatSmallTalkPatternService.match_category("sim") == "ack"
    assert ChatSmallTalkPatternService.match_category("sim quero") is None
