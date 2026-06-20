"""Testes do preset CHAT_LLM_LATENCY_PROFILE (Onda 11.2.2)."""

import importlib

from app.infrastructure.config.llm_latency_profile import (
    describe_active_profile,
    resolve_llm_max_tokens,
    resolve_ollama_num_ctx,
)


def _reload_settings(monkeypatch):
    monkeypatch.delenv("LLM_MAX_TOKENS", raising=False)
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)

    import app.infrastructure.config.llm_latency_profile as profile_module
    import app.infrastructure.config.settings as settings_module

    importlib.reload(profile_module)
    importlib.reload(settings_module)

    return settings_module.Settings


def test_operational_cpu_profile_defaults(monkeypatch):
    monkeypatch.setenv("CHAT_LLM_LATENCY_PROFILE", "operational_cpu")
    Settings = _reload_settings(monkeypatch)

    assert Settings.LLM_MAX_TOKENS == 320
    assert Settings.OLLAMA_NUM_CTX == 1024


def test_explicit_env_overrides_profile(monkeypatch):
    monkeypatch.setenv("CHAT_LLM_LATENCY_PROFILE", "operational_cpu")
    monkeypatch.setenv("LLM_MAX_TOKENS", "512")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "3072")

    assert resolve_llm_max_tokens() == 512
    assert resolve_ollama_num_ctx() == 3072


def test_unknown_profile_falls_back_to_balanced(monkeypatch):
    monkeypatch.setenv("CHAT_LLM_LATENCY_PROFILE", "desconhecido")
    monkeypatch.delenv("LLM_MAX_TOKENS", raising=False)
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)

    assert resolve_llm_max_tokens() == 768
    assert resolve_ollama_num_ctx() == 1536


def test_describe_active_profile(monkeypatch):
    monkeypatch.setenv("CHAT_LLM_LATENCY_PROFILE", "documental")
    monkeypatch.delenv("LLM_MAX_TOKENS", raising=False)
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)

    info = describe_active_profile()

    assert info["profile"] == "documental"
    assert info["llmMaxTokens"] == 768
    assert info["ollamaNumCtx"] == 4096
    assert info["llmMaxTokensExplicit"] is False
    assert "operational_cpu" in info["availableProfiles"]
