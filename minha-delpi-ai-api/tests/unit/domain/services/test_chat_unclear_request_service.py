from app.domain.services.chat_unclear_request_service import ChatUnclearRequestService


def test_classifies_vague_action_requests():
    assert ChatUnclearRequestService.classify("faz isso") == "action"
    assert ChatUnclearRequestService.classify("manda") == "action"


def test_classifies_vague_fix_requests():
    assert ChatUnclearRequestService.classify("arruma") == "fix"
    assert ChatUnclearRequestService.classify("ajusta isso") == "fix"


def test_classifies_bare_reference():
    assert ChatUnclearRequestService.classify("isso") == "reference"
    assert ChatUnclearRequestService.classify("aquilo") == "reference"
    assert ChatUnclearRequestService.classify("tira isso") == "reference"


def test_does_not_match_operational_or_long_messages():
    assert ChatUnclearRequestService.classify("estoque do produto 10080001") is None
    assert ChatUnclearRequestService.classify("coloque isso na lousa") is None
    assert ChatUnclearRequestService.classify("arruma o texto do e-mail") is None
    assert ChatUnclearRequestService.classify("") is None


def test_build_direct_answer_returns_clarification():
    answer = ChatUnclearRequestService.build_direct_answer(message="faz isso")
    assert answer is not None
    assert "não entendi" in answer.lower()


def test_build_direct_answer_with_options():
    answer = ChatUnclearRequestService.build_direct_answer(
        message="isso",
        with_options=True,
    )
    assert answer is not None
    assert "corrigir" in answer.lower()
