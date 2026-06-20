"""Presets de latência LLM por ambiente (Onda 11.2.2).

Variáveis explícitas (`LLM_MAX_TOKENS`, `OLLAMA_NUM_CTX`) sempre têm prioridade.
Use `CHAT_LLM_LATENCY_PROFILE` quando quiser um pacote calibrado sem ajustar cada valor.
"""

from __future__ import annotations

import os

_PROFILES: dict[str, dict[str, int]] = {
    # Homologação / dev operacional — meta ~50% menos latência vs balanced (jun/2026).
    "operational_cpu": {
        "llm_max_tokens": 320,
        "ollama_num_ctx": 1024,
    },
    # Default dev / equilíbrio qualidade-latência.
    "balanced": {
        "llm_max_tokens": 768,
        "ollama_num_ctx": 1536,
    },
    # Agentes documentais ou respostas mais longas (GPU ou 16GB+ RAM).
    "documental": {
        "llm_max_tokens": 768,
        "ollama_num_ctx": 4096,
    },
}

DEFAULT_PROFILE = "operational_cpu"


def _active_profile_name() -> str:
    return os.getenv("CHAT_LLM_LATENCY_PROFILE", DEFAULT_PROFILE).lower().strip()


def _profile_values(name: str) -> dict[str, int]:
    if name not in _PROFILES:
        return _PROFILES["balanced"]

    return _PROFILES[name]


def resolve_llm_max_tokens() -> int:
    explicit = os.getenv("LLM_MAX_TOKENS")

    if explicit is not None and str(explicit).strip() != "":
        return int(explicit)

    return _profile_values(_active_profile_name())["llm_max_tokens"]


def resolve_ollama_num_ctx() -> int:
    explicit = os.getenv("OLLAMA_NUM_CTX")

    if explicit is not None and str(explicit).strip() != "":
        return int(explicit)

    return _profile_values(_active_profile_name())["ollama_num_ctx"]


def describe_active_profile() -> dict[str, object]:
    name = _active_profile_name()
    preset = _profile_values(name)

    return {
        "profile": name,
        "llmMaxTokens": resolve_llm_max_tokens(),
        "ollamaNumCtx": resolve_ollama_num_ctx(),
        "llmMaxTokensExplicit": os.getenv("LLM_MAX_TOKENS") is not None,
        "ollamaNumCtxExplicit": os.getenv("OLLAMA_NUM_CTX") is not None,
        "presetLlmMaxTokens": preset["llm_max_tokens"],
        "presetOllamaNumCtx": preset["ollama_num_ctx"],
        "availableProfiles": sorted(_PROFILES.keys()),
    }
