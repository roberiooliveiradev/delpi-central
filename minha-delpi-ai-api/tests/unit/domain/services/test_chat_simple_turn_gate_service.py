from app.domain.services.chat_simple_turn_gate_service import (
    ChatSimpleTurnGateService,
)


def _intent(message: str, **kwargs):
    return ChatSimpleTurnGateService.evaluate(message=message, **kwargs)


def test_identity_question_is_simple_turn():
    decision = _intent("como vc s chama?")
    assert decision.matched is True
    assert decision.intent == "assistant_identity"
    assert decision.hide_activity is True
    assert decision.requires_tool is False
    assert decision.requires_rag is False


def test_greeting_is_simple_turn():
    assert _intent("ola").intent == "small_talk"
    assert _intent("bom dia").matched is True


def test_thanks_is_simple_turn():
    assert _intent("obg").matched is True
    assert _intent("vlw").matched is True


def test_utility_question_is_simple_turn():
    assert _intent("que horas sao?").intent == "utility"


def test_capabilities_question_is_simple_turn():
    assert _intent("o que voce pode fazer?").intent == "capabilities"


def test_unclear_request_is_simple_turn():
    assert _intent("faz isso").intent == "unclear_request"


def test_operational_query_is_not_simple_turn():
    decision = _intent("qual o estoque do produto 10080001?")
    assert decision.matched is False
    assert decision.hide_activity is False


def test_attachment_turn_is_not_simple():
    decision = _intent("resuma", attachment_ids=["att-1"])
    assert decision.matched is False


def test_is_simple_turn_helper():
    assert ChatSimpleTurnGateService.is_simple_turn(message="quem e voce") is True
    assert (
        ChatSimpleTurnGateService.is_simple_turn(
            message="liste os fornecedores do produto 10080001"
        )
        is False
    )
