from app.infrastructure.config.vision_llm_config import resolve_vision_llm_config


def test_openai_compatible_inherits_kimi_when_vision_vars_empty(monkeypatch):
    monkeypatch.setenv("VISION_LLM_PROVIDER", "openai_compatible")
    monkeypatch.delenv("VISION_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("VISION_LLM_MODEL", raising=False)
    monkeypatch.delenv("VISION_LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_TEXT_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_TEXT_MODEL", raising=False)
    monkeypatch.delenv("LLM_TEXT_API_KEY", raising=False)
    monkeypatch.setenv("KIMI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("KIMI_MODEL", "moonshotai/kimi-k3")
    monkeypatch.setenv("KIMI_API_KEY", "sk-or-test")

    config = resolve_vision_llm_config()

    assert config.provider == "openai_compatible"
    assert config.base_url == "https://openrouter.ai/api/v1"
    assert config.model == "moonshotai/kimi-k3"
    assert config.api_key == "sk-or-test"


def test_vision_llm_vars_override_kimi(monkeypatch):
    monkeypatch.setenv("VISION_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("VISION_LLM_BASE_URL", "https://vision.example/v1")
    monkeypatch.setenv("VISION_LLM_MODEL", "other-vlm")
    monkeypatch.setenv("VISION_LLM_API_KEY", "vision-key")
    monkeypatch.setenv("KIMI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("KIMI_MODEL", "moonshotai/kimi-k3")
    monkeypatch.setenv("KIMI_API_KEY", "sk-or-test")

    config = resolve_vision_llm_config()

    assert config.base_url == "https://vision.example/v1"
    assert config.model == "other-vlm"
    assert config.api_key == "vision-key"


def test_ollama_default_ignores_kimi_model(monkeypatch):
    monkeypatch.setenv("VISION_LLM_PROVIDER", "ollama")
    monkeypatch.delenv("VISION_LLM_MODEL", raising=False)
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_OLLAMA_MODEL", "qwen2.5vl:7b")
    monkeypatch.setenv("KIMI_MODEL", "moonshotai/kimi-k3")

    config = resolve_vision_llm_config()

    assert config.provider == "ollama"
    assert config.model == "qwen2.5vl:7b"
