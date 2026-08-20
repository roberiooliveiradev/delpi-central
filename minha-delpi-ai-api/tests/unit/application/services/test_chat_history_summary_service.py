from types import SimpleNamespace

from app.application.services.chat_history_summary_service import ChatHistorySummaryService
from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()


class _FakeLlm:
    def __init__(self):
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return "Resumo narrativo da conversa antiga."


def _messages(count: int):
    return [
        SimpleNamespace(role="user" if i % 2 == 0 else "assistant", content=f"msg-{i}")
        for i in range(count)
    ]


def test_build_preserved_facts_prefix_includes_memory_keys():
    prefix = ChatHistorySummaryService.build_preserved_facts_prefix(
        {
            "userCorrections": [{"content": "quero em tabela"}],
            "behaviorInstructions": {"responseFormat": "table"},
            "operationalFocus": {"productCode": "10080001", "branch": "01"},
            "conversationState": {
                "userCorrections": [{"content": "não é filiais, é SC"}],
            },
        }
    )

    assert "Correções do usuário" in prefix
    assert "quero em tabela" in prefix
    assert "não é filiais, é SC" in prefix
    assert "responseFormat=table" in prefix
    assert "productCode=10080001" in prefix
    assert "branch=01" in prefix


def test_ensure_preserved_facts_prepends_once():
    snapshot = {
        "behaviorInstructions": {"tone": "direct"},
        "operationalFocus": {"productCode": "90260015"},
    }
    first = ChatHistorySummaryService.ensure_preserved_facts("Resumo curto.", snapshot)
    second = ChatHistorySummaryService.ensure_preserved_facts(first, snapshot)

    assert first.count("Fatos preservados") == 1
    assert second == first
    assert second.startswith("Fatos preservados")
    assert "Resumo curto." in second


def test_prepare_history_passes_priority_facts_to_llm(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_HISTORY_SUMMARY_TRIGGER_MESSAGES",
        4,
    )
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_HISTORY_MAX_MESSAGES",
        2,
    )

    llm = _FakeLlm()
    service = ChatHistorySummaryService(
        llm_gateway=llm,
        intelligence_settings_service=SimpleNamespace(
            resolve=lambda: SimpleNamespace(chat_history_summary_enabled=True),
        ),
    )

    summary, recent = service.prepare_history(
        _messages(8),
        max_messages=2,
        memory_snapshot={
            "userCorrections": [{"content": "responda só com o saldo"}],
            "operationalFocus": {"productCode": "10080001"},
        },
    )

    assert len(recent) == 2
    assert "responda só com o saldo" in summary
    assert "productCode=10080001" in summary
    assert "Resumo narrativo" in summary
    assert llm.messages is not None
    user_content = llm.messages[1]["content"]
    assert "responda só com o saldo" in user_content
    assert "Fatos preservados" in user_content or "prioridade" in user_content.lower()
