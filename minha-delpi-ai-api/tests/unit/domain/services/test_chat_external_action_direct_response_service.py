from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.infrastructure.config.app_config_adapter import InfrastructureAppConfigAdapter
from app.infrastructure.config.settings import Settings


def test_should_skip_rag_when_external_action_ran():
    ChatExternalActionDirectResponseService.configure(InfrastructureAppConfigAdapter())

    assert ChatExternalActionDirectResponseService.should_skip_rag(
        {"skipRag": True, "directAnswer": None}
    )


def test_resolve_answer_returns_trimmed_text():
    ChatExternalActionDirectResponseService.configure(InfrastructureAppConfigAdapter())

    answer = ChatExternalActionDirectResponseService.resolve_answer(
        {"directAnswer": "  Produto 10080055: cabo.  "}
    )

    assert answer == "Produto 10080055: cabo."


def test_iter_stream_chunks_streams_small_pieces(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS", 3)
    monkeypatch.setattr(Settings, "CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS", 0)
    ChatExternalActionDirectResponseService.configure(InfrastructureAppConfigAdapter())

    chunks = list(
        ChatExternalActionDirectResponseService.iter_stream_chunks("Olá mundo")
    )

    assert chunks == ["Olá", " mu", "ndo"]


def test_iter_stream_chunks_uses_words_for_long_text(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS", 12)
    monkeypatch.setattr(Settings, "CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS", 0)
    ChatExternalActionDirectResponseService.configure(InfrastructureAppConfigAdapter())

    text = " ".join(f"palavra{i}" for i in range(30))
    chunks = list(ChatExternalActionDirectResponseService.iter_stream_chunks(text))

    assert len(chunks) > 3
    assert "".join(chunks) == text
    assert all(" " not in chunk.strip() or chunk.endswith(" ") for chunk in chunks[:-1])
