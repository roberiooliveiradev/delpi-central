from app.infrastructure.llm.llm_warmup_service import should_skip_warmup_for_provider


def test_should_skip_warmup_for_openai_compatible_aliases():
    for provider in ("vllm", "openai_compatible", "openai"):
        assert should_skip_warmup_for_provider(provider) is True


def test_should_not_skip_warmup_for_ollama():
    assert should_skip_warmup_for_provider("ollama") is False
