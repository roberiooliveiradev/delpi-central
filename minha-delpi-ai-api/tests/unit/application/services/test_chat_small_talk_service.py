import pytest

from app.application.services.chat_small_talk_service import ChatSmallTalkService
from app.domain.services.chat_fast_path_service import ChatFastPathService


@pytest.mark.parametrize(
    "message",
    [
        "ola",
        "olá",
        "oi",
        "bom dia",
        "obrigado",
        "valeu",
        "tchau",
        "ok",
        "olá, tudo bem?",
        "fala ai",
        "ate mais",
        "desculpa",
        "show",
        "kkk",
        "muito obrigada",
    ],
)
def test_small_talk_detection(message: str):
    assert ChatFastPathService.is_small_talk(message)
    assert ChatSmallTalkService.is_small_talk(message)
    assert ChatSmallTalkService.classify(message)


def test_small_talk_direct_answer_platform():
    answer = ChatSmallTalkService.build_direct_answer(
        message="ola",
        workspace_context={},
    )

    assert answer
    lowered = answer.lower()
    assert any(
        token in lowered
        for token in ("ajudar", "resolver", "perguntar", "olá", "oi", "pronto")
    )


def test_small_talk_direct_answer_agent():
    answer = ChatSmallTalkService.build_direct_answer(
        message="oi",
        workspace_context={
            "agent": {
                "name": "Agente Minha DELPI",
                "description": "assistente geral.",
            },
            "agentId": "11111111-1111-4111-8111-111111111111",
        },
    )

    assert answer
    assert "Agente Minha DELPI" in answer


def test_non_small_talk_is_not_classified():
    assert not ChatSmallTalkService.is_small_talk("estoque do produto 10080047")
    assert ChatSmallTalkService.classify("estoque do produto 10080047") is None
    assert not ChatSmallTalkService.is_small_talk("sim quero ver pedidos")


def test_apology_direct_answer():
    answer = ChatSmallTalkService.build_direct_answer(
        message="desculpa",
        workspace_context={},
    )

    assert answer
    lowered = answer.lower()
    assert any(
        token in lowered
        for token in ("sem problemas", "tranquilo", "tudo bem", "reformular")
    )


def test_praise_direct_answer():
    answer = ChatSmallTalkService.build_direct_answer(
        message="show",
        workspace_context={},
    )

    assert answer
    lowered = answer.lower()
    assert any(token in lowered for token in ("bom", "boa", "show", "feliz", "detalhar"))


def test_small_talk_variants_are_stable():
    first = ChatSmallTalkService.build_direct_answer(
        message="ola",
        workspace_context={},
    )
    second = ChatSmallTalkService.build_direct_answer(
        message="ola",
        workspace_context={},
    )

    assert first == second
