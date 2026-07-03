from __future__ import annotations

import os

from dataclasses import dataclass

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
    normalized = str(provider or "ollama").lower().strip()

    if normalized in {"off", "disabled", "none"}:
        return "off"

    if normalized in OPENAI_COMPATIBLE_VISION_PROVIDERS:
        return "openai_compatible"

    return "ollama"


def resolve_vision_llm_provider_name() -> str:
    return normalize_vision_llm_provider(_env("VISION_LLM_PROVIDER", "ollama"))


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_float(name: str, default: float) -> float:
    raw = _env(name, str(default))

    try:
        return float(raw)
    except ValueError:
        return default


def resolve_vision_llm_config() -> VisionLlmConfig:
    provider = resolve_vision_llm_provider_name()

    if provider == "openai_compatible":
        base_url = (
            _env("VISION_LLM_BASE_URL")
            or _env("LLM_TEXT_BASE_URL")
            or _env("VLLM_BASE_URL", "http://vllm:8000/v1")
        ).rstrip("/")
        model = (
            _env("VISION_LLM_MODEL")
            or _env("CHAT_DOCUMENT_VISION_OLLAMA_MODEL", "gpt-4o-mini")
        )
        api_key = _env("VISION_LLM_API_KEY") or _env("LLM_TEXT_API_KEY") or _env(
            "VLLM_API_KEY",
            "",
        )
        timeout = _env_float(
            "CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS",
            _env_float("OLLAMA_TIMEOUT_SECONDS", 300.0),
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
