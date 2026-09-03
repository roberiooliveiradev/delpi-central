from app.infrastructure.config.llm_stack_config import resolve_inherited_provider


def test_inherited_provider_falls_back_to_stack(monkeypatch):
    monkeypatch.delenv("TEST_AXIS_PROVIDER", raising=False)

    def normalize(value: str) -> str:
        return f"n:{value}"

    assert (
        resolve_inherited_provider(
            "TEST_AXIS_PROVIDER",
            normalize=normalize,
            stack_provider="openai_compatible",
        )
        == "n:openai_compatible"
    )


def test_inherited_provider_honors_explicit_env(monkeypatch):
    monkeypatch.setenv("TEST_AXIS_PROVIDER", "ollama")

    def normalize(value: str) -> str:
        return value

    assert (
        resolve_inherited_provider(
            "TEST_AXIS_PROVIDER",
            normalize=normalize,
            stack_provider="openai_compatible",
        )
        == "ollama"
    )
