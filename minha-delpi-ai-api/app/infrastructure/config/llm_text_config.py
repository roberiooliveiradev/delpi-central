from __future__ import annotations

import os

from app.domain.entities.llm_text_config import LlmTextConfig
from app.domain.services.chat_llm_provider_normalization_service import (
    ChatLlmProviderNormalizationService,
)


def normalize_llm_provider(provider: str) -> str:
    return ChatLlmProviderNormalizationService.normalize(provider)


def is_openai_compatible_provider(provider: str) -> bool:
    return ChatLlmProviderNormalizationService.is_openai_compatible(provider)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_float(name: str, default: float) -> float:
    raw = _env(name, str(default))

    try:
        return float(raw)
    except ValueError:
        return default


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = _env(name)
        if value:
            return value
    return default


def resolve_llm_provider_name() -> str:
    return normalize_llm_provider(_env("LLM_PROVIDER", "ollama"))


def resolve_llm_text_config() -> LlmTextConfig:
    """Resolve texto LLM.

    Com ``LLM_PROVIDER=openai_compatible``, a cadeia de credenciais é:

    ``LLM_TEXT_*`` → ``KIMI_*`` (mesmo token das atas / OpenRouter) → ``VLLM_*`` (legado).

    Em produção basta definir ``KIMI_*`` + ``LLM_PROVIDER=openai_compatible``.
    """
    provider = resolve_llm_provider_name()

    if provider == "openai_compatible":
        base_url = _first_env(
            "LLM_TEXT_BASE_URL",
            "KIMI_BASE_URL",
            "VLLM_BASE_URL",
            default="http://vllm:8000/v1",
        ).rstrip("/")
        model = _first_env(
            "LLM_TEXT_MODEL",
            "KIMI_MODEL",
            "VLLM_MODEL",
            default="Qwen/Qwen2.5-7B-Instruct",
        )
        api_key = _first_env(
            "LLM_TEXT_API_KEY",
            "KIMI_API_KEY",
            "VLLM_API_KEY",
            default="minha-delpi-local-vllm",
        )
        timeout = (
            _env_float("LLM_TEXT_TIMEOUT_SECONDS", 0.0)
            or _env_float("KIMI_TIMEOUT_SECONDS", 0.0)
            or _env_float("VLLM_TIMEOUT_SECONDS", 300.0)
        )
    else:
        base_url = (_env("LLM_TEXT_BASE_URL") or _env("OLLAMA_BASE_URL", "http://ollama:11434")).rstrip(
            "/"
        )
        model = _env("LLM_TEXT_MODEL") or _env("OLLAMA_MODEL", "qwen2.5:3b")
        api_key = _env("LLM_TEXT_API_KEY")
        timeout = _env_float("LLM_TEXT_TIMEOUT_SECONDS", 0.0) or _env_float(
            "OLLAMA_TIMEOUT_SECONDS",
            300.0,
        )

    return LlmTextConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        timeout_seconds=timeout,
    )
