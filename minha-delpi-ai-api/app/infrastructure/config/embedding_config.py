from __future__ import annotations

import os

from app.domain.entities.embedding_config import EmbeddingConfig
from app.infrastructure.config.llm_text_config import resolve_llm_provider_name

OPENAI_COMPATIBLE_EMBEDDING_PROVIDERS = frozenset(
    {"openai_compatible", "openai", "vllm"}
)

# Tags locais do Ollama — não são modelo de /v1/embeddings do stack Kimi/OpenRouter.
_LOCAL_OLLAMA_EMBEDDING_MODELS = frozenset(
    {
        "bge-m3",
        "nomic-embed-text",
        "mxbai-embed-large",
        "all-minilm",
        "snowflake-arctic-embed",
    }
)


def normalize_embedding_provider(provider: str) -> str:
    normalized = str(provider or "").lower().strip()

    if not normalized:
        return normalize_embedding_provider(resolve_llm_provider_name())

    if normalized in OPENAI_COMPATIBLE_EMBEDDING_PROVIDERS:
        return "openai_compatible"

    if normalized in {"off", "disabled", "none"}:
        return "off"

    return "ollama"


def resolve_embedding_provider_name() -> str:
    return resolve_embedding_config().provider


def _requested_embedding_provider() -> str:
    explicit = _env("EMBEDDING_PROVIDER")
    if explicit:
        return normalize_embedding_provider(explicit)
    return normalize_embedding_provider(resolve_llm_provider_name())


def _is_local_ollama_embedding_model(model: str) -> bool:
    tag = str(model or "").strip().lower()
    if not tag:
        return True
    base = tag.split(":", 1)[0]
    return base in _LOCAL_OLLAMA_EMBEDDING_MODELS


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


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = _env(name)
        if value:
            return value
    return default


def resolve_embedding_config() -> EmbeddingConfig:
    provider = _requested_embedding_provider()
    model = _env("EMBEDDING_MODEL")
    timeout = _env_float("EMBEDDING_TIMEOUT_SECONDS", 120.0)
    dimensions = _env_int("EMBEDDING_DIMENSIONS", 1024)

    if provider == "openai_compatible" and _is_local_ollama_embedding_model(model):
        return EmbeddingConfig(
            provider="off",
            base_url="",
            model=model,
            api_key="",
            timeout_seconds=timeout,
            dimensions=dimensions,
        )

    if provider == "off":
        return EmbeddingConfig(
            provider="off",
            base_url="",
            model=model,
            api_key="",
            timeout_seconds=timeout,
            dimensions=dimensions,
        )

    if provider == "openai_compatible":
        base_url = _first_env(
            "EMBEDDING_BASE_URL",
            "LLM_TEXT_BASE_URL",
            "KIMI_BASE_URL",
            "VLLM_BASE_URL",
            default="http://vllm:8000/v1",
        ).rstrip("/")
        api_key = _first_env(
            "EMBEDDING_API_KEY",
            "LLM_TEXT_API_KEY",
            "KIMI_API_KEY",
            "VLLM_API_KEY",
        )
        return EmbeddingConfig(
            provider=provider,
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout_seconds=timeout,
            dimensions=dimensions,
        )

    base_url = (_env("EMBEDDING_BASE_URL") or _env("OLLAMA_BASE_URL", "http://ollama:11434")).rstrip(
        "/"
    )
    return EmbeddingConfig(
        provider=provider,
        base_url=base_url,
        model=model or "bge-m3",
        api_key=_env("EMBEDDING_API_KEY"),
        timeout_seconds=timeout,
        dimensions=dimensions,
    )
