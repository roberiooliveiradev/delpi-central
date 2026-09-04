from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_user_query_improvement_service import (
    ChatUserQueryImprovementService,
)


class _FakeGateway:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[list[dict]] = []

    def generate(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        return self.reply

    def stream(self, messages: list[dict]):
        yield self.reply


def test_improve_descriao_applies_rules_without_llm():
    configure_domain_infrastructure_ports()
    ChatUserQueryImprovementService.configure(None)

    result = ChatUserQueryImprovementService.improve(
        "qual a descrião do 10050078?",
        response_mode="fast",
    )

    assert result.applied is True
    assert result.source == "rules"
    assert "descricao" in result.improved.lower() or "descrição" in result.improved.lower()
    assert "10050078" in result.improved
    assert result.message_for_intelligence != result.original or "descri" in result.improved


def test_improve_clean_description_is_noop():
    configure_domain_infrastructure_ports()
    ChatUserQueryImprovementService.configure(None)

    message = "qual a descrição do 10050078?"
    result = ChatUserQueryImprovementService.improve(message, response_mode="fast")

    assert result.applied is False
    assert result.reason in {"already_clean", "gate_closed", "llm_noop"}
    assert result.message_for_intelligence == message.strip()


def test_improve_unknown_typo_uses_llm_when_gated():
    """Irmão: typo fora das regras P14 (froenecedor) → LLM corrige."""
    configure_domain_infrastructure_ports()
    gateway = _FakeGateway("qual o fornecedor do 10050078?")
    ChatUserQueryImprovementService.configure(gateway)

    result = ChatUserQueryImprovementService.improve(
        "qual o froenecedor do 10050078?",
        response_mode="fast",
        llm_gateway=gateway,
    )

    assert result.applied is True
    assert result.source == "llm"
    assert "10050078" in result.improved
    assert "fornecedor" in result.improved.lower()


def test_improve_rejects_llm_that_drops_product_code(monkeypatch):
    configure_domain_infrastructure_ports()
    gateway = _FakeGateway("qual a descricao do produto?")
    ChatUserQueryImprovementService.configure(gateway)

    from app.domain.services import chat_user_query_improvement_service as mod

    monkeypatch.setattr(
        mod.ChatUserQueryImprovementService,
        "_gate_needs_llm",
        classmethod(lambda cls, message, product_code_hint=None: True),
    )

    result = ChatUserQueryImprovementService.improve(
        "qual a descrixao do 10050078?",
        response_mode="fast",
        llm_gateway=gateway,
    )

    assert result.applied is False
    assert result.reason == "llm_rejected_code_drop"
