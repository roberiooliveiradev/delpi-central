"""Testes do modo de resposta do chat (rápida / normal / pensador)."""

from app.domain.services.chat_response_mode_service import ChatResponseModeService


def test_normalize_aliases():
    assert ChatResponseModeService.normalize("rapida") == "fast"
    assert ChatResponseModeService.normalize("pensador") == "thinker"
    assert ChatResponseModeService.normalize(None) == "normal"
    assert ChatResponseModeService.normalize("unknown") == "normal"


def test_fast_mode_uses_smaller_limits(monkeypatch):
    monkeypatch.setenv("CHAT_RESPONSE_MODE_FAST_MODEL", "qwen2.5:1.5b")
    monkeypatch.setenv("CHAT_RESPONSE_MODE_FAST_MAX_TOKENS", "256")
    config = ChatResponseModeService.resolve("fast")
    assert config.response_mode == "fast"
    assert config.model == "qwen2.5:1.5b"
    assert config.max_tokens == 256


def test_thinker_mode_expands_context(monkeypatch):
    monkeypatch.setenv("CHAT_RESPONSE_MODE_THINKER_NUM_CTX", "4096")
    config = ChatResponseModeService.resolve("thinker")
    assert config.response_mode == "thinker"
    assert config.num_ctx == 4096


def test_list_modes_when_enabled(monkeypatch):
    monkeypatch.setenv("CHAT_RESPONSE_MODES_ENABLED", "true")
    modes = ChatResponseModeService.list_modes()
    assert len(modes) == 3
    assert {item["id"] for item in modes} == {"fast", "normal", "thinker"}
