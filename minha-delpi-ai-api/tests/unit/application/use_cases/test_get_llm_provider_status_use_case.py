from app.application.use_cases.get_llm_provider_status_use_case import (
    GetLlmProviderStatusUseCase,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.infrastructure.config.app_config_adapter import InfrastructureAppConfigAdapter


def test_execute_returns_text_embedding_and_vision_sections(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "vllm")
    monkeypatch.setenv("VLLM_BASE_URL", "https://api.test/v1")
    monkeypatch.setenv("VLLM_MODEL", "gpt-test")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setenv("EMBEDDING_MODEL", "bge-m3")
    monkeypatch.setenv("VISION_LLM_PROVIDER", "ollama")

    ChatDomainConfigService.configure(InfrastructureAppConfigAdapter())

    payload = GetLlmProviderStatusUseCase().execute()

    assert payload["provider"] == "openai_compatible"
    assert payload["model"] == "gpt-test"
    assert payload["text"]["provider"] == "openai_compatible"
    assert payload["text"]["baseUrl"] == "https://api.test/v1"
    assert payload["embedding"]["provider"] == "ollama"
    assert payload["embedding"]["model"] == "bge-m3"
    assert payload["vision"]["provider"] == "ollama"
