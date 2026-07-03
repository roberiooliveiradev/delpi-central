from __future__ import annotations

import os

from app.domain.entities.embedding_config import EmbeddingConfig

OPENAI_COMPATIBLE_EMBEDDING_PROVIDERS = frozenset(
    {"openai_compatible", "openai", "vllm"}
)


def normalize_embedding_provider(provider: str) -> str:
    normalized = str(provider or "ollama").lower().strip()

    if normalized in OPENAI_COMPATIBLE_EMBEDDING_PROVIDERS:
        return "openai_compatible"

    if normalized in {"off", "disabled", "none"}:
        return "off"

    return "ollama"


def resolve_embedding_provider_name() -> str:
    return normalize_embedding_provider(_env("EMBEDDING_PROVIDER", "ollama"))


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_float(name: str, default: float) -> float:
    raw = _env(name, str(default))

    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = _env(name, str(default))

    try:
        return int(raw)
    except ValueError:
        return default


def resolve_embedding_config() -> EmbeddingConfig:
    provider = resolve_embedding_provider_name()

    if provider == "openai_compatible":
        base_url = (
            _env("EMBEDDING_BASE_URL")
            or _env("LLM_TEXT_BASE_URL")
            or _env("VLLM_BASE_URL", "http://vllm:8000/v1")
        ).rstrip("/")
        model = _env("EMBEDDING_MODEL", "text-embedding-3-small")
        api_key = _env("EMBEDDING_API_KEY") or _env("LLM_TEXT_API_KEY") or _env(
            "VLLM_API_KEY",
            "",
        )
        timeout = _env_float("EMBEDDING_TIMEOUT_SECONDS", 120.0)
    else:
        base_url = (_env("EMBEDDING_BASE_URL") or _env("OLLAMA_BASE_URL", "http://ollama:11434")).rstrip(
            "/"
        )
        model = _env("EMBEDDING_MODEL", "bge-m3")
        api_key = _env("EMBEDDING_API_KEY")
        timeout = _env_float("EMBEDDING_TIMEOUT_SECONDS", 120.0)

    return EmbeddingConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        timeout_seconds=timeout,
        dimensions=_env_int("EMBEDDING_DIMENSIONS", 1024),
    )
