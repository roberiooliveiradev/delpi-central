from __future__ import annotations

import os

from dataclasses import dataclass

from app.infrastructure.config.llm_stack_config import resolve_inherited_provider
from app.infrastructure.config.llm_text_config import resolve_llm_provider_name

OPENAI_COMPATIBLE_VISION_PROVIDERS = frozenset(
    {"openai_compatible", "openai", "vllm"}
)


@dataclass(frozen=True)
class VisionLlmConfig:
    provider: str
    base_url: str
    model: str
    api_key: str
    timeout_seconds: float


def normalize_vision_llm_provider(provider: str) -> str:
    normalized = str(provider or "").lower().strip()

    if not normalized:
        return normalize_vision_llm_provider(resolve_llm_provider_name())

    if normalized in {"off", "disabled", "none"}:
        return "off"

    if normalized in OPENAI_COMPATIBLE_VISION_PROVIDERS:
        return "openai_compatible"

    return "ollama"


def resolve_vision_llm_provider_name() -> str:
    return resolve_vision_llm_config().provider


def _requested_vision_provider() -> str:
    return resolve_inherited_provider(
        "VISION_LLM_PROVIDER",
        normalize=normalize_vision_llm_provider,
        stack_provider=resolve_llm_provider_name(),
    )


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


def resolve_vision_llm_config() -> VisionLlmConfig:
    """Resolve VLM.

    Com ``VISION_LLM_PROVIDER=openai_compatible``, a cadeia de credenciais é:

    ``VISION_LLM_*`` → ``LLM_TEXT_*`` → ``KIMI_*`` (mesmo token do chat/atas) → ``VLLM_*``.

    Em produção basta ``KIMI_*`` + ``VISION_LLM_PROVIDER=openai_compatible`` (mesmo modelo
    multimodal do texto, ex. ``moonshotai/kimi-k3``).
    """
    provider = _requested_vision_provider()

    if provider == "openai_compatible":
        base_url = _first_env(
            "VISION_LLM_BASE_URL",
            "LLM_TEXT_BASE_URL",
            "KIMI_BASE_URL",
            "VLLM_BASE_URL",
            default="http://vllm:8000/v1",
        ).rstrip("/")
        model = _first_env(
            "VISION_LLM_MODEL",
            "LLM_TEXT_MODEL",
            "KIMI_MODEL",
            "VLLM_MODEL",
            default="gpt-4o-mini",
        )
        api_key = _first_env(
            "VISION_LLM_API_KEY",
            "LLM_TEXT_API_KEY",
            "KIMI_API_KEY",
            "VLLM_API_KEY",
            default="",
        )
        timeout = (
            _env_float("VISION_LLM_TIMEOUT_SECONDS", 0.0)
            or _env_float("CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS", 0.0)
            or _env_float("KIMI_TIMEOUT_SECONDS", 0.0)
            or _env_float("OLLAMA_TIMEOUT_SECONDS", 300.0)
        )
    else:
        base_url = (
            _env("VISION_LLM_BASE_URL")
            or _env("CHAT_DOCUMENT_VISION_OLLAMA_BASE_URL")
            or _env("OLLAMA_BASE_URL", "http://ollama:11434")
        ).rstrip("/")
        model = (
            _env("VISION_LLM_MODEL")
            or _env("CHAT_DOCUMENT_VISION_OLLAMA_MODEL", "qwen2.5vl:7b")
        )
        api_key = _env("VISION_LLM_API_KEY")
        timeout = _env_float(
            "CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS",
            _env_float("OLLAMA_TIMEOUT_SECONDS", 300.0),
        )

    return VisionLlmConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        timeout_seconds=timeout,
    )
